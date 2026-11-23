#include <jni.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static void close_extra_fds(int keep_fd) {
    DIR *dir = opendir("/proc/self/fd");
    if (dir != NULL) {
        int dir_fd = dirfd(dir);
        struct dirent *entry;
        while ((entry = readdir(dir)) != NULL) {
            if (entry->d_name[0] < '0' || entry->d_name[0] > '9') {
                continue;
            }
            int fd = atoi(entry->d_name);
            if (fd > 2 && fd != keep_fd && fd != dir_fd) {
                close(fd);
            }
        }
        closedir(dir);
        return;
    }

    long max_fd = sysconf(_SC_OPEN_MAX);
    if (max_fd < 0 || max_fd > 4096) {
        max_fd = 1024;
    }
    for (int fd = 3; fd < (int)max_fd; fd++) {
        if (fd != keep_fd) {
            close(fd);
        }
    }
}

JNIEXPORT jintArray JNICALL
Java_com_auralink_vpn_TunExec_spawnWithFd(
    JNIEnv *env,
    jclass clazz,
    jstring jBinPath,
    jobjectArray jArgs,
    jint tunFd,
    jint targetFd
) {
    (void)clazz;
    if (jBinPath == NULL || jArgs == NULL || tunFd < 0 || targetFd < 3) {
        return NULL;
    }

    const char *bin_path_raw = (*env)->GetStringUTFChars(env, jBinPath, NULL);
    if (bin_path_raw == NULL) {
        return NULL;
    }
    char *bin_path = strdup(bin_path_raw);
    (*env)->ReleaseStringUTFChars(env, jBinPath, bin_path_raw);

    jsize argc = (*env)->GetArrayLength(env, jArgs);
    char **argv = (char **)calloc((size_t)argc + 1, sizeof(char *));
    if (argv == NULL || bin_path == NULL) {
        free(bin_path);
        free(argv);
        return NULL;
    }

    for (jsize i = 0; i < argc; i++) {
        jstring jarg = (jstring)(*env)->GetObjectArrayElement(env, jArgs, i);
        if (jarg != NULL) {
            const char *s = (*env)->GetStringUTFChars(env, jarg, NULL);
            argv[i] = s ? strdup(s) : strdup("");
            if (s) {
                (*env)->ReleaseStringUTFChars(env, jarg, s);
            }
            (*env)->DeleteLocalRef(env, jarg);
        } else {
            argv[i] = strdup("");
        }
    }
    argv[argc] = NULL;

    int logpipe[2] = {-1, -1};
    if (pipe(logpipe) != 0) {
        for (jsize i = 0; i < argc; i++) free(argv[i]);
        free(argv);
        free(bin_path);
        return NULL;
    }
    fcntl(logpipe[0], F_SETFD, FD_CLOEXEC);
    fcntl(logpipe[1], F_SETFD, FD_CLOEXEC);

    pid_t pid = fork();
    if (pid < 0) {
        close(logpipe[0]);
        close(logpipe[1]);
        for (jsize i = 0; i < argc; i++) free(argv[i]);
        free(argv);
        free(bin_path);
        return NULL;
    }

    if (pid == 0) {
        /* Child process: preserve TUN FD at targetFd (O_RDWR, FD_CLOEXEC cleared) */
        setsid();

        int src_tun = (int)tunFd;
        int dst_tun = (int)targetFd;
        if (src_tun == logpipe[1] || src_tun <= 2) {
            src_tun = dup(src_tun);
        }

        int devnull = open("/dev/null", O_RDONLY);
        if (devnull >= 0) {
            dup2(devnull, STDIN_FILENO);
            if (devnull > 2) close(devnull);
        }

        dup2(logpipe[1], STDOUT_FILENO);
        dup2(logpipe[1], STDERR_FILENO);

        if (src_tun == dst_tun) {
            int flags = fcntl(dst_tun, F_GETFD);
            if (flags >= 0) {
                fcntl(dst_tun, F_SETFD, flags & ~FD_CLOEXEC);
            }
        } else {
            if (dup2(src_tun, dst_tun) < 0) {
                dprintf(STDERR_FILENO, "tunexec: dup2(%d, %d) failed: %s\n", src_tun, dst_tun, strerror(errno));
                _exit(126);
            }
            /* Ensure FD_CLOEXEC is definitely cleared on dst_tun */
            int flags = fcntl(dst_tun, F_GETFD);
            if (flags >= 0) {
                fcntl(dst_tun, F_SETFD, flags & ~FD_CLOEXEC);
            }
        }

        close_extra_fds(dst_tun);

        execv(bin_path, argv);
        dprintf(STDERR_FILENO, "tunexec: execv(%s) failed: %s\n", bin_path, strerror(errno));
        _exit(127);
    }

    /* Parent process */
    close(logpipe[1]);
    for (jsize i = 0; i < argc; i++) free(argv[i]);
    free(argv);
    free(bin_path);

    jintArray out = (*env)->NewIntArray(env, 2);
    if (out == NULL) {
        close(logpipe[0]);
        return NULL;
    }
    jint pair[2] = {(jint)pid, (jint)logpipe[0]};
    (*env)->SetIntArrayRegion(env, out, 0, 2, pair);
    return out;
}

JNIEXPORT jboolean JNICALL
Java_com_auralink_vpn_TunExec_isAlive(JNIEnv *env, jclass clazz, jint pid) {
    (void)env;
    (void)clazz;
    if (pid <= 0) {
        return JNI_FALSE;
    }
    int status = 0;
    pid_t res = waitpid((pid_t)pid, &status, WNOHANG);
    if (res == (pid_t)pid || (res < 0 && errno == ECHILD)) {
        return JNI_FALSE;
    }
    return (kill((pid_t)pid, 0) == 0) ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT void JNICALL
Java_com_auralink_vpn_TunExec_killProcess(JNIEnv *env, jclass clazz, jint pid) {
    (void)env;
    (void)clazz;
    if (pid <= 0) {
        return;
    }
    kill(-(pid_t)pid, SIGTERM);
    kill((pid_t)pid, SIGTERM);

    int status = 0;
    for (int i = 0; i < 6; i++) {
        pid_t res = waitpid((pid_t)pid, &status, WNOHANG);
        if (res == (pid_t)pid || (res < 0 && errno == ECHILD)) {
            return;
        }
        usleep(25000);
    }

    kill(-(pid_t)pid, SIGKILL);
    kill((pid_t)pid, SIGKILL);
    waitpid((pid_t)pid, &status, WNOHANG);
}

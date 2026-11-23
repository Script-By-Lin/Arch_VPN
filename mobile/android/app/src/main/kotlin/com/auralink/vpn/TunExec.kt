package com.auralink.vpn

/**
 * Native JNI helper that spawns `libtun2socks.so` using `fork()` + `dup2(tunFd, 3)` + `execv()`,
 * bypassing Java's `ProcessBuilder` which closes all file descriptors > 2 before `execve()`.
 */
object TunExec {
    init {
        System.loadLibrary("tunexec")
    }

    /**
     * Spawns [binPath] with [args], mapping [tunFd] onto [targetFd] (default 3, O_RDWR, no CLOEXEC).
     * Returns an IntArray of `[pid, logPipeReadFd]`, or null on failure.
     */
    @JvmStatic
    external fun spawnWithFd(
        binPath: String,
        args: Array<String>,
        tunFd: Int,
        targetFd: Int = 3
    ): IntArray?

    @JvmStatic
    external fun isAlive(pid: Int): Boolean

    @JvmStatic
    external fun killProcess(pid: Int)
}

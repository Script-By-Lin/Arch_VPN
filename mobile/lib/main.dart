import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'screens/free_keys_screen.dart';
import 'screens/home_screen.dart';
import 'screens/logs_screen.dart';
import 'screens/servers_screen.dart';
import 'screens/settings_screen.dart';
import 'services/vpn_controller.dart';
import 'theme/daylight_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const AuraLinkMobileApp());
}

class AuraLinkMobileApp extends StatelessWidget {
  const AuraLinkMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider<VpnController>(
      create: (_) => VpnController()..initialize(),
      child: MaterialApp(
        title: 'AuraLink VPN',
        debugShowCheckedModeBanner: false,
        theme: DaylightTheme.build(),
        home: const _MainShell(),
      ),
    );
  }
}

class _MainShell extends StatefulWidget {
  const _MainShell();

  @override
  State<_MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<_MainShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      HomeScreen(onOpenServers: () => setState(() => _index = 2)),
      FreeKeysScreen(onJumpToTunnel: () => setState(() => _index = 0)),
      const ServersScreen(),
      const LogsScreen(),
      const SettingsScreen(),
    ];

    return Scaffold(
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: DaylightColors.border)),
        ),
        child: NavigationBar(
          selectedIndex: _index,
          onDestinationSelected: (i) => setState(() => _index = i),
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.shield_outlined),
              selectedIcon: Icon(Icons.shield_rounded),
              label: 'Tunnel',
            ),
            NavigationDestination(
              icon: Icon(Icons.public_outlined),
              selectedIcon: Icon(Icons.public_rounded),
              label: 'Free',
            ),
            NavigationDestination(
              icon: Icon(Icons.dns_outlined),
              selectedIcon: Icon(Icons.dns_rounded),
              label: 'Nodes',
            ),
            NavigationDestination(
              icon: Icon(Icons.terminal_outlined),
              selectedIcon: Icon(Icons.terminal_rounded),
              label: 'Logs',
            ),
            NavigationDestination(
              icon: Icon(Icons.tune_outlined),
              selectedIcon: Icon(Icons.tune_rounded),
              label: 'Settings',
            ),
          ],
        ),
      ),
    );
  }
}

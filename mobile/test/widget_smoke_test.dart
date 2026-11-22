import 'package:auralink_vpn/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('AuraLinkMobileApp renders all 5 tabs cleanly without overflow or exceptions',
      (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.binding.setSurfaceSize(const Size(412, 915));

    await tester.pumpWidget(const AuraLinkMobileApp());
    await tester.pump(const Duration(milliseconds: 250));

    // Tab 1: Tunnel (Home)
    expect(find.text('AuraLink'), findsOneWidget);
    expect(find.text('INTERACTIVE TUNNEL MODEL'), findsOneWidget);
    expect(find.text('DOWNLOAD'), findsOneWidget);
    expect(find.text('UPLOAD'), findsOneWidget);

    // Tab 2: Free Regions
    await tester.tap(find.text('Free'));
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('Free Regions'), findsOneWidget);

    // Tab 3: Nodes (Servers)
    await tester.tap(find.text('Nodes'));
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('VPN Nodes'), findsOneWidget);

    // Tab 4: Logs
    await tester.tap(find.text('Logs'));
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('>_ Log Stream'), findsOneWidget);

    // Tab 5: Settings
    await tester.tap(find.text('Settings'));
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('Tunnel & Network Settings'), findsOneWidget);
    expect(find.text('IPv6 Leak Shield'), findsOneWidget);
    expect(find.text('MOBILE FREE KEYS ADMIN BACKEND'), findsOneWidget);

    await tester.binding.setSurfaceSize(null);
  });
}

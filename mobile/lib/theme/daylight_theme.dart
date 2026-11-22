import 'package:flutter/material.dart';

/// AuraLink Daylight Light Theme palette — matches the Linux Desktop GUI (`gui/theme.py`).
class DaylightColors {
  static const Color bgMain = Color(0xFFF1F5F9);
  static const Color bgSurface = Color(0xFFFFFFFF);
  static const Color bgCard = Color(0xFFF8FAFC);
  static const Color bgCardHover = Color(0xFFEFF6FF);

  static const Color border = Color(0xFFE2E8F0);
  static const Color borderLight = Color(0xFFCBD5E1);

  static const Color primary = Color(0xFF0284C7);
  static const Color primaryDark = Color(0xFF0369A1);
  static const Color primarySoft = Color(0xFFE0F2FE);
  static const Color primaryBorder = Color(0xFFBAE6FD);

  static const Color success = Color(0xFF059669);
  static const Color successBright = Color(0xFF10B981);
  static const Color successDark = Color(0xFF047857);
  static const Color successSoft = Color(0xFFECFDF5);
  static const Color successBorder = Color(0xFFA7F3D0);

  static const Color warning = Color(0xFFD97706);
  static const Color warningBright = Color(0xFFF59E0B);
  static const Color warningDark = Color(0xFFB45309);
  static const Color warningSoft = Color(0xFFFFFBEB);
  static const Color warningBorder = Color(0xFFFDE68A);

  static const Color danger = Color(0xFFDC2626);
  static const Color dangerBright = Color(0xFFEF4444);
  static const Color dangerDark = Color(0xFFB91C1C);
  static const Color dangerSoft = Color(0xFFFEF2F2);
  static const Color dangerBorder = Color(0xFFFCA5A5);

  static const Color textPrimary = Color(0xFF0F172A);
  static const Color textSecondary = Color(0xFF475569);
  static const Color textMuted = Color(0xFF64748B);
  static const Color textSubtle = Color(0xFF94A3B8);
}

class DaylightTheme {
  static ThemeData build() {
    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: DaylightColors.bgMain,
      colorScheme: ColorScheme.fromSeed(
        seedColor: DaylightColors.primary,
        brightness: Brightness.light,
        surface: DaylightColors.bgSurface,
        primary: DaylightColors.primary,
        secondary: DaylightColors.success,
        error: DaylightColors.danger,
      ),
    );

    return base.copyWith(
      appBarTheme: const AppBarTheme(
        backgroundColor: DaylightColors.bgMain,
        foregroundColor: DaylightColors.textPrimary,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: DaylightColors.bgSurface,
        indicatorColor: DaylightColors.primarySoft,
        elevation: 0,
        height: 66,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(
            fontSize: 11,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
            color: selected ? DaylightColors.primaryDark : DaylightColors.textMuted,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return IconThemeData(
            size: 22,
            color: selected ? DaylightColors.primary : DaylightColors.textMuted,
          );
        }),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: DaylightColors.bgSurface,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        hintStyle: const TextStyle(
          color: DaylightColors.textSubtle,
          fontSize: 13,
          fontFamily: 'monospace',
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: DaylightColors.borderLight),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: DaylightColors.borderLight),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: DaylightColors.primary, width: 1.6),
        ),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected) ? Colors.white : DaylightColors.textSubtle,
        ),
        trackColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected) ? DaylightColors.successBright : DaylightColors.border,
        ),
      ),
    );
  }
}

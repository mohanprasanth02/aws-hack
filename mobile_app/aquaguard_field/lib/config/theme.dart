import 'package:flutter/material.dart';

class AquaTheme {
  // Deep Obsidian & Cyber Slate Surfaces
  static const Color bgDark = Color(0xFF070B14);
  static const Color bgCanvas = Color(0xFF04060A);
  static const Color surfaceCard = Color(0xFF0E1626);
  static const Color surfaceCardHover = Color(0xFF152238);
  static const Color surfaceElevated = Color(0xFF19253C);
  static const Color surfaceInput = Color(0xFF0A0F1D);

  // Neon & Cyber Accents
  static const Color iceCyan = Color(0xFF00F2FE);
  static const Color electricBlue = Color(0xFF38BDF8);
  static const Color platinumWhite = Color(0xFFF8FAFC);
  static const Color titaniumSilver = Color(0xFFE2E8F0);
  static const Color titaniumMuted = Color(0xFF94A3B8);
  static const Color textWhite = Color(0xFFFFFFFF);
  static const Color textMuted = Color(0xFF94A3B8);
  static const Color textSubtle = Color(0xFF64748B);

  // Status & Telemetry Accents
  static const Color emeraldGreen = Color(0xFF10B981);
  static const Color emeraldBg = Color(0x1F10B981);
  static const Color solarAmber = Color(0xFFF59E0B);
  static const Color solarAmberBg = Color(0x1FF59E0B);
  static const Color criticalRed = Color(0xFFEF4444);
  static const Color criticalRedBg = Color(0x1FEF4444);
  static const Color iceCyanBg = Color(0x1F00F2FE);

  // Subtle Borders
  static const Color borderLight = Color(0x14FFFFFF); // 8% white
  static const Color borderMedium = Color(0x28FFFFFF); // 16% white
  static const Color borderCyan = Color(0x5500F2FE); // glowing cyan

  // Custom Gradients
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [Color(0xFF00F2FE), Color(0xFF38BDF8)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient cardGradient = LinearGradient(
    colors: [Color(0xFF111A2E), Color(0xFF0B1322)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient heroGradient = LinearGradient(
    colors: [Color(0xFF1E2D4A), Color(0xFF0D172A)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static ThemeData darkTheme = ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: bgDark,
    primaryColor: iceCyan,
    fontFamily: 'Inter',
    colorScheme: const ColorScheme.dark(
      primary: iceCyan,
      secondary: electricBlue,
      surface: surfaceCard,
      error: criticalRed,
      onPrimary: Color(0xFF050607),
      onSurface: textWhite,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.transparent,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        color: textWhite,
        fontSize: 16,
        fontWeight: FontWeight.w800,
        letterSpacing: 0.6,
      ),
      iconTheme: IconThemeData(color: titaniumSilver),
    ),
    cardTheme: CardTheme(
      color: surfaceCard,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: borderLight, width: 1),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: iceCyan,
        foregroundColor: const Color(0xFF050607),
        elevation: 0,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        textStyle: const TextStyle(
          fontWeight: FontWeight.w800,
          fontSize: 13,
          letterSpacing: 0.3,
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: iceCyan,
        side: const BorderSide(color: borderCyan, width: 1.2),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        textStyle: const TextStyle(
          fontWeight: FontWeight.w700,
          fontSize: 12.5,
          letterSpacing: 0.3,
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: surfaceInput,
      hintStyle: const TextStyle(color: textSubtle, fontSize: 13),
      labelStyle: const TextStyle(color: textMuted, fontSize: 13),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: borderLight),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: borderLight),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: iceCyan, width: 1.5),
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: surfaceElevated,
      contentTextStyle: const TextStyle(color: platinumWhite, fontSize: 13),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      behavior: SnackBarBehavior.floating,
    ),
  );
}

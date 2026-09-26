import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'config/theme.dart';
import 'screens/login_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Set cyber dark system status bar styling
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: AquaTheme.bgDark,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  runApp(const AquaGuardFieldApp());
}

class AquaGuardFieldApp extends StatelessWidget {
  const AquaGuardFieldApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AquaGuard Field',
      debugShowCheckedModeBanner: false,
      theme: AquaTheme.darkTheme,
      home: const LoginScreen(),
    );
  }
}

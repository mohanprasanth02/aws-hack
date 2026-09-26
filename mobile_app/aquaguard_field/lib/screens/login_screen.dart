import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../config/api_config.dart';
import '../config/theme.dart';
import '../services/api_service.dart';
import 'task_feed_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> with SingleTickerProviderStateMixin {
  final TextEditingController _emailController = TextEditingController(text: 'worker@aquaguard.io');
  final TextEditingController _passwordController = TextEditingController(text: 'Worker123!');
  final TextEditingController _serverController = TextEditingController(text: ApiConfig.baseUrl);

  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _showServerConfig = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeOutCubic,
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.06),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeOutCubic,
    ));
    _fadeController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _serverController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    HapticFeedback.lightImpact();
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    if (_serverController.text.trim().isNotEmpty) {
      ApiConfig.customBaseUrl = _serverController.text.trim();
    }

    final success = await ApiService.login(
      _emailController.text.trim(),
      _passwordController.text.trim(),
    );

    setState(() {
      _isLoading = false;
    });

    if (success) {
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        PageRouteBuilder(
          transitionDuration: const Duration(milliseconds: 400),
          pageBuilder: (_, __, ___) => const TaskFeedScreen(),
          transitionsBuilder: (_, animation, __, child) {
            return FadeTransition(
              opacity: animation,
              child: child,
            );
          },
        ),
      );
    } else {
      HapticFeedback.heavyImpact();
      setState(() {
        _errorMessage = 'Unable to reach core server (${ApiConfig.baseUrl}). Check Wi-Fi connection.';
      });
    }
  }

  void _quickFillDemo() {
    HapticFeedback.selectionClick();
    setState(() {
      _emailController.text = 'worker@aquaguard.io';
      _passwordController.text = 'Worker123!';
      _errorMessage = null;
    });
    _handleLogin();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AquaTheme.bgDark,
      body: Stack(
        children: [
          // Cyber Ambient Glow Spheres
          Positioned(
            top: -60,
            right: -60,
            child: Container(
              width: 260,
              height: 260,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AquaTheme.iceCyan.withOpacity(0.06),
              ),
            ),
          ),
          Positioned(
            bottom: -80,
            left: -80,
            child: Container(
              width: 280,
              height: 280,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AquaTheme.electricBlue.withOpacity(0.05),
              ),
            ),
          ),

          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 20.0),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 420),
                  child: FadeTransition(
                    opacity: _fadeAnimation,
                    child: SlideTransition(
                      position: _slideAnimation,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // Modern Glowing Hexagon App Badge
                          Center(
                            child: Container(
                              width: 76,
                              height: 76,
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  colors: [Color(0xFF13233D), Color(0xFF0C1525)],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                borderRadius: BorderRadius.circular(24),
                                border: Border.all(color: AquaTheme.iceCyan.withOpacity(0.4), width: 1.5),
                                boxShadow: [
                                  BoxShadow(
                                    color: AquaTheme.iceCyan.withOpacity(0.18),
                                    blurRadius: 24,
                                    offset: const Offset(0, 8),
                                  ),
                                ],
                              ),
                              child: const Center(
                                child: Icon(
                                  Icons.water_drop_rounded,
                                  color: AquaTheme.iceCyan,
                                  size: 38,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 18),

                          // Brand Headings
                          const Text(
                            'AQUAGUARD FIELD',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 2.0,
                              color: AquaTheme.platinumWhite,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Container(
                                width: 6,
                                height: 6,
                                decoration: const BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: AquaTheme.emeraldGreen,
                                ),
                              ),
                              const SizedBox(width: 6),
                              const Text(
                                'CAMPUS DISPATCH & VERIFICATION CORE',
                                style: TextStyle(
                                  fontSize: 10.5,
                                  fontWeight: FontWeight.w700,
                                  color: AquaTheme.textMuted,
                                  letterSpacing: 0.8,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 24),

                          // Login Card
                          Container(
                            padding: const EdgeInsets.all(22),
                            decoration: BoxDecoration(
                              color: AquaTheme.surfaceCard,
                              borderRadius: BorderRadius.circular(22),
                              border: Border.all(color: AquaTheme.borderLight),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.45),
                                  blurRadius: 24,
                                  offset: const Offset(0, 10),
                                ),
                              ],
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                const Text(
                                  'TECHNICIAN ACCESS',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 1.2,
                                    color: AquaTheme.iceCyan,
                                  ),
                                ),
                                const SizedBox(height: 16),

                                // Email Input
                                TextField(
                                  controller: _emailController,
                                  keyboardType: TextInputType.emailAddress,
                                  style: const TextStyle(color: AquaTheme.platinumWhite, fontSize: 13.5),
                                  decoration: InputDecoration(
                                    prefixIcon: const Icon(Icons.person_pin_outlined, color: AquaTheme.titaniumSilver, size: 20),
                                    labelText: 'Technician Email',
                                    hintText: 'worker@aquaguard.io',
                                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                                  ),
                                ),
                                const SizedBox(height: 12),

                                // Password Input
                                TextField(
                                  controller: _passwordController,
                                  obscureText: _obscurePassword,
                                  style: const TextStyle(color: AquaTheme.platinumWhite, fontSize: 13.5),
                                  decoration: InputDecoration(
                                    prefixIcon: const Icon(Icons.lock_outline_rounded, color: AquaTheme.titaniumSilver, size: 20),
                                    labelText: 'Security Password',
                                    hintText: '••••••••',
                                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                                    suffixIcon: IconButton(
                                      icon: Icon(
                                        _obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                                        color: AquaTheme.textMuted,
                                        size: 18,
                                      ),
                                      onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 16),

                                // Server Config Expander
                                GestureDetector(
                                  onTap: () {
                                    HapticFeedback.selectionClick();
                                    setState(() => _showServerConfig = !_showServerConfig);
                                  },
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                    decoration: BoxDecoration(
                                      color: Colors.white.withOpacity(0.03),
                                      borderRadius: BorderRadius.circular(10),
                                      border: Border.all(color: Colors.white.withOpacity(0.06)),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(
                                          Icons.dns_rounded,
                                          size: 14,
                                          color: _showServerConfig ? AquaTheme.iceCyan : AquaTheme.textMuted,
                                        ),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: Text(
                                            'Core Server: ${ApiConfig.baseUrl}',
                                            style: const TextStyle(
                                              fontSize: 11,
                                              fontFamily: 'monospace',
                                              color: AquaTheme.textMuted,
                                            ),
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ),
                                        Icon(
                                          _showServerConfig ? Icons.expand_less_rounded : Icons.expand_more_rounded,
                                          size: 18,
                                          color: AquaTheme.textMuted,
                                        ),
                                      ],
                                    ),
                                  ),
                                ),

                                if (_showServerConfig) ...[
                                  const SizedBox(height: 10),
                                  TextField(
                                    controller: _serverController,
                                    style: const TextStyle(color: AquaTheme.platinumWhite, fontSize: 12, fontFamily: 'monospace'),
                                    decoration: InputDecoration(
                                      prefixIcon: const Icon(Icons.settings_input_antenna_rounded, color: AquaTheme.iceCyan, size: 16),
                                      labelText: 'Server URL (Host:Port)',
                                      hintText: 'https://aws-hack.onrender.com',
                                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                                    ),
                                  ),
                                ],

                                if (_errorMessage != null) ...[
                                  const SizedBox(height: 14),
                                  Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: AquaTheme.criticalRedBg,
                                      borderRadius: BorderRadius.circular(10),
                                      border: Border.all(color: AquaTheme.criticalRed.withOpacity(0.3)),
                                    ),
                                    child: Row(
                                      children: [
                                        const Icon(Icons.info_outline_rounded, color: AquaTheme.criticalRed, size: 16),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: Text(
                                            _errorMessage!,
                                            style: const TextStyle(color: AquaTheme.criticalRed, fontSize: 11.5),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],

                                const SizedBox(height: 20),

                                // Login Button
                                Container(
                                  decoration: BoxDecoration(
                                    gradient: AquaTheme.primaryGradient,
                                    borderRadius: BorderRadius.circular(14),
                                    boxShadow: [
                                      BoxShadow(
                                        color: AquaTheme.iceCyan.withOpacity(0.25),
                                        blurRadius: 14,
                                        offset: const Offset(0, 4),
                                      ),
                                    ],
                                  ),
                                  child: ElevatedButton(
                                    onPressed: _isLoading ? null : _handleLogin,
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.transparent,
                                      shadowColor: Colors.transparent,
                                      foregroundColor: const Color(0xFF050607),
                                      padding: const EdgeInsets.symmetric(vertical: 14),
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                                    ),
                                    child: _isLoading
                                        ? const SizedBox(
                                            height: 18,
                                            width: 18,
                                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                                          )
                                        : const Row(
                                            mainAxisAlignment: MainAxisAlignment.center,
                                            children: [
                                              Icon(Icons.login_rounded, size: 18),
                                              SizedBox(width: 8),
                                              Text(
                                                'ACCESS WORK ORDERS',
                                                style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13, letterSpacing: 0.5),
                                              ),
                                            ],
                                          ),
                                  ),
                                ),

                                const SizedBox(height: 12),

                                // 1-Tap Demo Fill
                                OutlinedButton.icon(
                                  onPressed: _isLoading ? null : _quickFillDemo,
                                  icon: const Icon(Icons.bolt_rounded, size: 16, color: AquaTheme.solarAmber),
                                  label: const Text(
                                    '1-Tap Demo Technician Login',
                                    style: TextStyle(fontSize: 12, color: AquaTheme.platinumWhite, fontWeight: FontWeight.w600),
                                  ),
                                  style: OutlinedButton.styleFrom(
                                    padding: const EdgeInsets.symmetric(vertical: 11),
                                    side: BorderSide(color: Colors.white.withOpacity(0.12)),
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 24),
                          const Center(
                            child: Text(
                              'SNS Real-Time Campus Infrastructure Sensor Network',
                              style: TextStyle(fontSize: 11, color: AquaTheme.textSubtle),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

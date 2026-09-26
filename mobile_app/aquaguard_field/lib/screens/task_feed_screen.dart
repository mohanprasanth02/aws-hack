import 'dart:async';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_staggered_animations/flutter_staggered_animations.dart';
import '../config/theme.dart';
import '../models/work_order_model.dart';
import '../services/api_service.dart';
import 'route_navigation_screen.dart';
import 'photo_completion_screen.dart';
import 'login_screen.dart';

class TaskFeedScreen extends StatefulWidget {
  const TaskFeedScreen({super.key});

  @override
  State<TaskFeedScreen> createState() => _TaskFeedScreenState();
}

class _TaskFeedScreenState extends State<TaskFeedScreen> with TickerProviderStateMixin {
  List<WorkOrder> _tasks = [];
  bool _isLoading = true;
  bool _isDispatching = false;
  String _selectedFilter = 'All';

  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  Timer? _autoRefreshTimer;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 0.85, end: 1.15).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _loadTasks();

    // Real-time synchronization every 4 seconds with web console
    _autoRefreshTimer = Timer.periodic(const Duration(seconds: 4), (_) {
      if (mounted && !_isDispatching && !_isLoading) {
        _silentPollTasks();
      }
    });
  }

  @override
  void dispose() {
    _autoRefreshTimer?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _silentPollTasks() async {
    final tasks = await ApiService.fetchTasks(activeOnly: false);
    if (mounted) {
      setState(() {
        _tasks = tasks;
      });
    }
  }

  Future<void> _resetAllTasks() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AquaTheme.surfaceElevated,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Reset All Work Orders?', style: TextStyle(color: AquaTheme.platinumWhite, fontWeight: FontWeight.bold)),
        content: const Text('This will remove all work orders and return both Web and Mobile to clean zero state.', style: TextStyle(color: AquaTheme.textMuted)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel', style: TextStyle(color: AquaTheme.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AquaTheme.criticalRed),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Reset All', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (confirm != true) return;

    HapticFeedback.heavyImpact();
    setState(() => _isLoading = true);
    final success = await ApiService.resetAllTasks();
    final tasks = await ApiService.fetchTasks(activeOnly: false);
    if (mounted) {
      setState(() {
        _tasks = tasks;
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'System Reload: All work orders cleared across Web and Mobile.' : 'Failed to reset work orders.'),
          backgroundColor: AquaTheme.surfaceElevated,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Future<void> _loadTasks() async {
    setState(() => _isLoading = true);
    final tasks = await ApiService.fetchTasks(activeOnly: false);
    if (mounted) {
      setState(() {
        _tasks = tasks;
        _isLoading = false;
      });
    }
  }

  Future<void> _triggerAutoDispatch() async {
    HapticFeedback.mediumImpact();
    setState(() => _isDispatching = true);

    final success = await ApiService.triggerAutoDispatch();
    final updatedTasks = await ApiService.fetchTasks(activeOnly: false);

    if (mounted) {
      setState(() {
        _isDispatching = false;
        _tasks = updatedTasks;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.flash_on_rounded, color: AquaTheme.solarAmber, size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  success
                      ? 'Live Risk Scan: Dispatched ${updatedTasks.length} real-time work orders!'
                      : 'Updated work orders from live telemetry grid.',
                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                ),
              ),
            ],
          ),
          backgroundColor: AquaTheme.surfaceElevated,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }

  Future<void> _cycleTaskStatus(WorkOrder task) async {
    HapticFeedback.lightImpact();
    String nextStatus;
    if (task.status == 'Dispatched') {
      nextStatus = 'En Route';
    } else if (task.status == 'En Route') {
      nextStatus = 'In Progress';
    } else {
      nextStatus = 'In Progress';
    }

    final success = await ApiService.updateStatus(task.id, nextStatus);
    if (success && mounted) {
      setState(() {
        task.status = nextStatus;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Updated ${task.ticketId} to $nextStatus. Live synchronized with web.'),
          backgroundColor: AquaTheme.surfaceElevated,
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
    }
  }

  List<WorkOrder> get _filteredTasks {
    if (_selectedFilter == 'Active') {
      return _tasks.where((t) => t.status != 'Resolved').toList();
    } else if (_selectedFilter == 'Resolved') {
      return _tasks.where((t) => t.status == 'Resolved').toList();
    }
    return _tasks;
  }

  Color _getPriorityColor(String priority) {
    switch (priority.toLowerCase()) {
      case 'emergency':
      case 'critical':
        return AquaTheme.criticalRed;
      case 'high':
        return AquaTheme.solarAmber;
      case 'medium':
        return AquaTheme.iceCyan;
      default:
        return AquaTheme.textMuted;
    }
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'resolved':
        return AquaTheme.emeraldGreen;
      case 'in progress':
        return AquaTheme.titaniumSilver;
      case 'en route':
        return AquaTheme.iceCyan;
      default:
        return AquaTheme.solarAmber;
    }
  }

  @override
  Widget build(BuildContext context) {
    final totalActive = _tasks.where((t) => t.status != 'Resolved').length;
    final totalLossLph = _tasks
        .where((t) => t.status != 'Resolved')
        .fold(0.0, (acc, item) => acc + item.estimatedLeakLph);
    final totalWaterSaved = _tasks
        .where((t) => t.status == 'Resolved')
        .fold(0.0, (acc, item) => acc + item.waterSavedLiters);

    return Scaffold(
      backgroundColor: AquaTheme.bgDark,
      body: Stack(
        children: [
          // Background ambient gradient
          Positioned(
            top: -60,
            left: -60,
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AquaTheme.iceCyan.withOpacity(0.03),
              ),
            ),
          ),

          SafeArea(
            child: NestedScrollView(
              physics: const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics()),
              headerSliverBuilder: (context, innerBoxIsScrolled) => [
                // iOS Frosted Glass App Bar
                SliverAppBar(
                  pinned: true,
                  floating: true,
                  elevation: 0,
                  backgroundColor: AquaTheme.bgDark.withOpacity(0.85),
                  flexibleSpace: ClipRRect(
                    child: BackdropFilter(
                      filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
                      child: Container(color: Colors.transparent),
                    ),
                  ),
                  title: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'FIELD WORK LOAD',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.2,
                          color: AquaTheme.platinumWhite,
                        ),
                      ),
                      Text(
                        ApiService.workerName,
                        style: const TextStyle(fontSize: 11, color: AquaTheme.textMuted, fontWeight: FontWeight.w400),
                      ),
                    ],
                  ),
                  actions: [
                    // Action: Auto-Dispatch from Risk
                    IconButton(
                      icon: _isDispatching
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2, color: AquaTheme.solarAmber),
                            )
                          : const Icon(Icons.flash_on_rounded, size: 21, color: AquaTheme.solarAmber),
                      tooltip: 'Auto-Dispatch from Live Risk',
                      onPressed: _isDispatching ? null : _triggerAutoDispatch,
                    ),
                    // Action: Live Sync
                    IconButton(
                      icon: const Icon(Icons.sync_rounded, size: 21, color: AquaTheme.titaniumSilver),
                      tooltip: 'Sync with Central Core',
                      onPressed: _loadTasks,
                    ),
                    // Action: Reload / Clear All Data
                    IconButton(
                      icon: const Icon(Icons.delete_sweep_rounded, size: 21, color: AquaTheme.criticalRed),
                      tooltip: 'Reload & Clear All Data',
                      onPressed: _resetAllTasks,
                    ),
                    // Action: Sign Out
                    IconButton(
                      icon: const Icon(Icons.logout_rounded, size: 18, color: AquaTheme.textSubtle),
                      tooltip: 'Sign Out',
                      onPressed: () {
                        HapticFeedback.lightImpact();
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(builder: (context) => const LoginScreen()),
                        );
                      },
                    ),
                  ],
                ),

                // Live Telemetry Sync Pill & Top Metrics
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                    child: Column(
                      children: [
                        // Live Telemetry Pill
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.03),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: Colors.white.withOpacity(0.08)),
                          ),
                          child: Row(
                            children: [
                              AnimatedBuilder(
                                animation: _pulseAnimation,
                                builder: (context, child) => Transform.scale(
                                  scale: _pulseAnimation.value,
                                  child: Container(
                                    width: 8,
                                    height: 8,
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      color: _tasks.isEmpty ? AquaTheme.solarAmber : AquaTheme.emeraldGreen,
                                      boxShadow: [
                                        BoxShadow(
                                          color: (_tasks.isEmpty ? AquaTheme.solarAmber : AquaTheme.emeraldGreen).withOpacity(0.6),
                                          blurRadius: 6,
                                          spreadRadius: 1,
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Text(
                                _tasks.isEmpty
                                    ? 'CAMPUS GRID • STANDBY FOR AUTO-DISPATCH'
                                    : 'CAMPUS GRID • LIVE ACTIVE SYNC',
                                style: TextStyle(
                                  fontFamily: 'monospace',
                                  fontSize: 10.5,
                                  fontWeight: FontWeight.w700,
                                  color: _tasks.isEmpty ? AquaTheme.solarAmber : AquaTheme.emeraldGreen,
                                  letterSpacing: 0.6,
                                ),
                              ),
                              const Spacer(),
                              Text(
                                '${_filteredTasks.length} Tickets',
                                style: const TextStyle(fontSize: 11, color: AquaTheme.textMuted, fontWeight: FontWeight.w600),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 12),

                        // 3 iOS-Style Metric Cards
                        Row(
                          children: [
                            Expanded(
                              child: _buildIosMetricCard(
                                label: 'ACTIVE LEAKS',
                                value: '$totalActive',
                                subtitle: 'Dispatched',
                                color: AquaTheme.solarAmber,
                                icon: Icons.warning_amber_rounded,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: _buildIosMetricCard(
                                label: 'LOSS RATE',
                                value: '${totalLossLph.toStringAsFixed(0)} L/h',
                                subtitle: 'Est. loss',
                                color: AquaTheme.criticalRed,
                                icon: Icons.water_damage_outlined,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: _buildIosMetricCard(
                                label: 'WATER SAVED',
                                value: '${(totalWaterSaved / 1000).toStringAsFixed(1)} kL',
                                subtitle: 'Verified',
                                color: AquaTheme.emeraldGreen,
                                icon: Icons.eco_outlined,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),

                        // Cupertino Segmented Filter Control
                        Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.04),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: Colors.white.withOpacity(0.06)),
                          ),
                          child: Row(
                            children: ['All', 'Active', 'Resolved'].map((filter) {
                              final isSelected = _selectedFilter == filter;
                              return Expanded(
                                child: GestureDetector(
                                  onTap: () {
                                    HapticFeedback.selectionClick();
                                    setState(() => _selectedFilter = filter);
                                  },
                                  child: AnimatedContainer(
                                    duration: const Duration(milliseconds: 200),
                                    curve: Curves.easeOutCubic,
                                    padding: const EdgeInsets.symmetric(vertical: 8),
                                    decoration: BoxDecoration(
                                      color: isSelected ? Colors.white.withOpacity(0.12) : Colors.transparent,
                                      borderRadius: BorderRadius.circular(10),
                                      border: isSelected
                                          ? Border.all(color: Colors.white.withOpacity(0.18), width: 0.8)
                                          : null,
                                      boxShadow: isSelected
                                          ? [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 8)]
                                          : null,
                                    ),
                                    child: Center(
                                      child: Text(
                                        filter,
                                        style: TextStyle(
                                          fontSize: 12.5,
                                          fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                                          color: isSelected ? AquaTheme.platinumWhite : AquaTheme.textMuted,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              );
                            }).toList(),
                          ),
                        ),
                        const SizedBox(height: 8),
                      ],
                    ),
                  ),
                ),
              ],
              body: RefreshIndicator(
                onRefresh: _loadTasks,
                color: AquaTheme.platinumWhite,
                backgroundColor: AquaTheme.surfaceCard,
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator(color: AquaTheme.platinumWhite))
                    : _filteredTasks.isEmpty
                        ? _buildAppleEmptyState()
                        : AnimationLimiter(
                            child: ListView.builder(
                              physics: const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics()),
                              padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
                              itemCount: _filteredTasks.length,
                              itemBuilder: (context, index) {
                                final task = _filteredTasks[index];
                                return AnimationConfiguration.staggeredList(
                                  position: index,
                                  duration: const Duration(milliseconds: 400),
                                  child: SlideAnimation(
                                    verticalOffset: 25.0,
                                    curve: Curves.easeOutCubic,
                                    child: FadeInAnimation(
                                      curve: Curves.easeOutCubic,
                                      child: _buildTaskCard(task),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // Apple-Inspired Empty State with Direct Auto-Dispatch Trigger
  Widget _buildAppleEmptyState() {
    return Center(
      child: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 40),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 400),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Pulsing Radar Shield Graphic
              AnimatedBuilder(
                animation: _pulseAnimation,
                builder: (context, child) => Container(
                  width: 88,
                  height: 88,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withOpacity(0.03),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.12 * _pulseAnimation.value),
                      width: 1.5,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: AquaTheme.solarAmber.withOpacity(0.12 * _pulseAnimation.value),
                        blurRadius: 30,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: const Center(
                    child: Icon(
                      Icons.shield_outlined,
                      color: AquaTheme.platinumWhite,
                      size: 40,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 22),

              const Text(
                'Zero Active Work Orders',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: AquaTheme.platinumWhite,
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(height: 8),

              const Text(
                'Campus water pipeline telemetry is operating nominally. Tap below to scan live risk telemetry anomalies and auto-dispatch work orders.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 12.5,
                  color: AquaTheme.textMuted,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 26),

              // Glowing Hero Auto-Dispatch Action Button
              ElevatedButton(
                onPressed: _isDispatching ? null : _triggerAutoDispatch,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AquaTheme.platinumWhite,
                  foregroundColor: const Color(0xFF050607),
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 15),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  elevation: 6,
                  shadowColor: Colors.white.withOpacity(0.25),
                ),
                child: _isDispatching
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                      )
                    : const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.bolt_rounded, size: 20),
                          SizedBox(width: 8),
                          Text(
                            'AUTO-DISPATCH FROM LIVE RISK',
                            style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 0.6, fontSize: 13),
                          ),
                        ],
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // Work Order Card with Apple iOS Styling
  Widget _buildTaskCard(WorkOrder task) {
    final priorityColor = _getPriorityColor(task.priority);
    final statusColor = _getStatusColor(task.status);
    final isResolved = task.status == 'Resolved';

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      decoration: BoxDecoration(
        color: AquaTheme.surfaceCard,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isResolved
              ? AquaTheme.emeraldGreen.withOpacity(0.3)
              : task.priority.toLowerCase() == 'emergency'
                  ? AquaTheme.criticalRed.withOpacity(0.35)
                  : Colors.white.withOpacity(0.08),
          width: 1.0,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.4),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Row: Ticket ID + Meter ID + Priority & Status Chips
            Row(
              children: [
                Text(
                  task.ticketId,
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontWeight: FontWeight.w800,
                    fontSize: 13,
                    color: AquaTheme.platinumWhite,
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.white.withOpacity(0.08)),
                  ),
                  child: Text(
                    task.meterId,
                    style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: AquaTheme.textMuted),
                  ),
                ),
                const Spacer(),
                // Priority Badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: priorityColor.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: priorityColor.withOpacity(0.35)),
                  ),
                  child: Text(
                    task.priority.toUpperCase(),
                    style: TextStyle(
                      fontSize: 9.5,
                      fontWeight: FontWeight.w700,
                      color: priorityColor,
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                // Status Badge (Interactive: Tap to cycle status)
                InkWell(
                  onTap: isResolved ? null : () => _cycleTaskStatus(task),
                  borderRadius: BorderRadius.circular(8),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusColor.withOpacity(0.14),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: statusColor.withOpacity(0.4)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 5,
                          height: 5,
                          decoration: BoxDecoration(shape: BoxShape.circle, color: statusColor),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          task.status.toUpperCase(),
                          style: TextStyle(
                            fontSize: 9.5,
                            fontWeight: FontWeight.w800,
                            color: statusColor,
                            letterSpacing: 0.3,
                          ),
                        ),
                        if (!isResolved) ...[
                          const SizedBox(width: 3),
                          Icon(Icons.sync_alt_rounded, size: 10, color: statusColor.withOpacity(0.8)),
                        ],
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Work Order Title
            Text(
              task.title,
              style: const TextStyle(
                fontSize: 14.5,
                fontWeight: FontWeight.w700,
                color: AquaTheme.platinumWhite,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 6),

            // Location
            Row(
              children: [
                const Icon(Icons.location_on_outlined, size: 14, color: AquaTheme.textMuted),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    task.location,
                    style: const TextStyle(fontSize: 12, color: AquaTheme.textMuted),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Telemetry Metric Bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: AquaTheme.surfaceElevated.withOpacity(0.6),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white.withOpacity(0.06)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('EST. WATER LOSS', style: TextStyle(fontSize: 9, color: AquaTheme.textSubtle, fontWeight: FontWeight.w700)),
                      Text(
                        '${task.estimatedLeakLph} L/h',
                        style: const TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: AquaTheme.criticalRed,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      const Text('ASSET CATEGORY', style: TextStyle(fontSize: 9, color: AquaTheme.textSubtle, fontWeight: FontWeight.w700)),
                      Text(
                        task.assetType,
                        style: const TextStyle(fontSize: 11.5, color: AquaTheme.titaniumSilver, fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            if (isResolved) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AquaTheme.emeraldBg,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AquaTheme.emeraldGreen.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle_rounded, size: 16, color: AquaTheme.emeraldGreen),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '+${task.waterSavedLiters.toStringAsFixed(0)} L Conserved • Photo Verified',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AquaTheme.emeraldGreen,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 14),

            // Interactive Actions Bar (Mobile Optimized: 2 balanced touch targets, zero RenderFlex overflow)
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () {
                      HapticFeedback.lightImpact();
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => RouteNavigationScreen(task: task)),
                      );
                    },
                    icon: const Icon(Icons.near_me_rounded, size: 15, color: AquaTheme.iceCyan),
                    label: const Text('GPS Route', style: TextStyle(color: AquaTheme.iceCyan, fontSize: 12, fontWeight: FontWeight.w700)),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 11),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      side: const BorderSide(color: AquaTheme.borderCyan),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: isResolved
                        ? () async {
                            HapticFeedback.lightImpact();
                            await Navigator.push(
                              context,
                              MaterialPageRoute(builder: (context) => PhotoCompletionScreen(task: task)),
                            );
                          }
                        : () async {
                            HapticFeedback.lightImpact();
                            final updated = await Navigator.push(
                              context,
                              MaterialPageRoute(builder: (context) => PhotoCompletionScreen(task: task)),
                            );
                            if (updated == true) {
                              _loadTasks();
                            }
                          },
                    icon: Icon(
                      isResolved ? Icons.verified_rounded : Icons.camera_alt_rounded,
                      size: 15,
                      color: isResolved ? AquaTheme.emeraldGreen : const Color(0xFF050607),
                    ),
                    label: Text(
                      isResolved ? 'View Proof' : 'Upload Proof',
                      style: TextStyle(
                        fontSize: 12,
                        color: isResolved ? AquaTheme.emeraldGreen : const Color(0xFF050607),
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: isResolved ? AquaTheme.surfaceElevated : AquaTheme.iceCyan,
                      padding: const EdgeInsets.symmetric(vertical: 11),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: isResolved ? 0 : 4,
                      shadowColor: AquaTheme.iceCyan.withOpacity(0.35),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // iOS Frosted Glass Mini Metric Tile
  Widget _buildIosMetricCard({
    required String label,
    required String value,
    required String subtitle,
    required Color color,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AquaTheme.surfaceCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                label,
                style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: color, letterSpacing: 0.5),
              ),
              Icon(icon, size: 14, color: color.withOpacity(0.7)),
            ],
          ),
          const SizedBox(height: 5),
          Text(
            value,
            style: const TextStyle(
              fontSize: 13.5,
              fontWeight: FontWeight.w800,
              color: AquaTheme.platinumWhite,
              fontFamily: 'monospace',
            ),
          ),
          const SizedBox(height: 2),
          Text(
            subtitle,
            style: const TextStyle(fontSize: 9, color: AquaTheme.textSubtle),
          ),
        ],
      ),
    );
  }
}

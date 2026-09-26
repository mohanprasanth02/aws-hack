import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config/theme.dart';
import '../models/work_order_model.dart';
import '../services/api_service.dart';
import '../services/location_service.dart';
import 'photo_completion_screen.dart';

class RouteNavigationScreen extends StatefulWidget {
  final WorkOrder task;

  const RouteNavigationScreen({super.key, required this.task});

  @override
  State<RouteNavigationScreen> createState() => _RouteNavigationScreenState();
}

class _RouteNavigationScreenState extends State<RouteNavigationScreen> with SingleTickerProviderStateMixin {
  LatLng _workerPosition = const LatLng(11.1005, 77.0258);
  late LatLng _targetMeterPosition;
  double _distanceMeters = 0.0;
  final MapController _mapController = MapController();
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _targetMeterPosition = LatLng(widget.task.latitude, widget.task.longitude);
    _initLiveLocation();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 0.9, end: 1.25).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _initLiveLocation() async {
    final pos = await LocationService.getCurrentLocation();
    if (mounted) {
      setState(() {
        _workerPosition = pos;
        _distanceMeters = LocationService.calculateDistanceMeters(_workerPosition, _targetMeterPosition);
      });
    }
  }

  Future<void> _markEnRoute() async {
    HapticFeedback.lightImpact();
    final success = await ApiService.updateStatus(widget.task.id, 'En Route');
    if (mounted) {
      widget.task.status = 'En Route';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'Status updated to EN ROUTE. Central web dashboard notified.' : 'Status updated locally.'),
          backgroundColor: AquaTheme.surfaceElevated,
          duration: const Duration(seconds: 2),
        ),
      );
      setState(() {});
    }
  }

  Future<void> _markInProgress() async {
    HapticFeedback.lightImpact();
    final success = await ApiService.updateStatus(widget.task.id, 'In Progress');
    if (mounted) {
      widget.task.status = 'In Progress';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? 'Status updated to IN PROGRESS. Central web dashboard notified.' : 'Status updated locally.'),
          backgroundColor: AquaTheme.surfaceElevated,
          duration: const Duration(seconds: 2),
        ),
      );
      setState(() {});
    }
  }

  Future<void> _launchExternalGoogleMaps() async {
    HapticFeedback.selectionClick();
    final url = Uri.parse(
      'https://www.google.com/maps/dir/?api=1&destination=${widget.task.latitude},${widget.task.longitude}&travelmode=walking',
    );
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    final etaMinutes = (_distanceMeters / 80).clamp(1, 45).round();

    return Scaffold(
      backgroundColor: AquaTheme.bgDark,
      appBar: AppBar(
        title: const Text('CAMPUS GPS ROUTE'),
        actions: [
          IconButton(
            icon: const Icon(Icons.my_location_rounded, size: 20),
            onPressed: () {
              HapticFeedback.selectionClick();
              _mapController.move(_workerPosition, 16.5);
            },
            tooltip: 'Center on My Location',
          ),
          IconButton(
            icon: const Icon(Icons.map_outlined, size: 20),
            onPressed: _launchExternalGoogleMaps,
            tooltip: 'Open in Google Maps',
          ),
        ],
      ),
      body: Stack(
        children: [
          // FlutterMap
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: LatLng(
                (_workerPosition.latitude + _targetMeterPosition.latitude) / 2,
                (_workerPosition.longitude + _targetMeterPosition.longitude) / 2,
              ),
              initialZoom: 16.5,
              minZoom: 14.0,
              maxZoom: 19.0,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.aquaguard.field',
              ),

              // Polyline connecting Worker to Risk Meter
              PolylineLayer(
                polylines: [
                  Polyline(
                    points: [
                      _workerPosition,
                      LatLng(
                        (_workerPosition.latitude + _targetMeterPosition.latitude) / 2,
                        (_workerPosition.longitude + _targetMeterPosition.longitude) / 2,
                      ),
                      _targetMeterPosition,
                    ],
                    strokeWidth: 4.5,
                    color: AquaTheme.iceCyan,
                    isDotted: true,
                  ),
                ],
              ),

              // Markers
              MarkerLayer(
                markers: [
                  // Worker Marker
                  Marker(
                    point: _workerPosition,
                    width: 44,
                    height: 44,
                    child: Container(
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: AquaTheme.surfaceCard,
                        border: Border.all(color: AquaTheme.iceCyan, width: 2.5),
                        boxShadow: [
                          BoxShadow(
                            color: AquaTheme.iceCyan.withOpacity(0.4),
                            blurRadius: 12,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                      child: const Icon(Icons.directions_walk_rounded, color: AquaTheme.iceCyan, size: 22),
                    ),
                  ),

                  // Target Risk Meter Marker with Animated Pulse
                  Marker(
                    point: _targetMeterPosition,
                    width: 54,
                    height: 54,
                    child: AnimatedBuilder(
                      animation: _pulseAnimation,
                      builder: (context, child) => Transform.scale(
                        scale: _pulseAnimation.value,
                        child: Container(
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: AquaTheme.criticalRed,
                            border: Border.all(color: Colors.white, width: 2.5),
                            boxShadow: [
                              BoxShadow(
                                color: AquaTheme.criticalRed.withOpacity(0.6),
                                blurRadius: 18,
                                spreadRadius: 3,
                              ),
                            ],
                          ),
                          child: const Icon(Icons.warning_amber_rounded, color: Colors.white, size: 26),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),

          // Floating Top Pill: Target Asset
          Positioned(
            top: 14,
            left: 16,
            right: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: AquaTheme.surfaceCard.withOpacity(0.92),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AquaTheme.borderLight),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.4),
                    blurRadius: 16,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      color: AquaTheme.solarAmber,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'TARGET: ${widget.task.ticketId} • ${widget.task.assetType}',
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: AquaTheme.platinumWhite,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                    decoration: BoxDecoration(
                      color: AquaTheme.solarAmberBg,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      widget.task.priority.toUpperCase(),
                      style: const TextStyle(fontSize: 9.5, fontWeight: FontWeight.bold, color: AquaTheme.solarAmber),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Floating Bottom Navigation HUD
          Positioned(
            left: 16,
            right: 16,
            bottom: 20,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AquaTheme.surfaceCard,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AquaTheme.borderMedium),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.6),
                    blurRadius: 24,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Destination & Walking Distance
                  Row(
                    children: [
                      Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          color: AquaTheme.surfaceElevated,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AquaTheme.borderCyan),
                        ),
                        child: const Icon(Icons.navigation_rounded, color: AquaTheme.iceCyan, size: 20),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.task.location,
                              style: const TextStyle(
                                fontSize: 13.5,
                                fontWeight: FontWeight.w800,
                                color: AquaTheme.platinumWhite,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '${widget.task.meterId} • Est. Leak: ${widget.task.estimatedLeakLph} L/h',
                              style: const TextStyle(fontSize: 11, color: AquaTheme.textMuted),
                            ),
                          ],
                        ),
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            '${_distanceMeters.toStringAsFixed(0)} m',
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w800,
                              fontFamily: 'monospace',
                              color: AquaTheme.platinumWhite,
                            ),
                          ),
                          Text(
                            '~$etaMinutes min walk',
                            style: const TextStyle(fontSize: 11, color: AquaTheme.emeraldGreen, fontWeight: FontWeight.w700),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // Actions row
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _launchExternalGoogleMaps,
                          icon: const Icon(Icons.directions_rounded, size: 16),
                          label: const Text('Google Maps', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            side: const BorderSide(color: AquaTheme.borderLight),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Container(
                          decoration: BoxDecoration(
                            gradient: AquaTheme.primaryGradient,
                            borderRadius: BorderRadius.circular(12),
                            boxShadow: [
                              BoxShadow(
                                color: AquaTheme.iceCyan.withOpacity(0.25),
                                blurRadius: 10,
                                offset: const Offset(0, 3),
                              ),
                            ],
                          ),
                          child: ElevatedButton.icon(
                            onPressed: () {
                              if (widget.task.status == 'In Progress') {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(builder: (context) => PhotoCompletionScreen(task: widget.task)),
                                );
                              } else if (widget.task.status == 'En Route') {
                                _markInProgress();
                              } else {
                                _markEnRoute();
                              }
                            },
                            icon: Icon(
                              widget.task.status == 'In Progress'
                                  ? Icons.camera_alt_rounded
                                  : widget.task.status == 'En Route'
                                      ? Icons.build_rounded
                                      : Icons.check_circle_outline_rounded,
                              size: 16,
                              color: const Color(0xFF050607),
                            ),
                            label: Text(
                              widget.task.status == 'In Progress'
                                  ? 'Upload Proof'
                                  : widget.task.status == 'En Route'
                                      ? 'Start Work'
                                      : 'Mark En Route',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                                color: Color(0xFF050607),
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.transparent,
                              shadowColor: Colors.transparent,
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

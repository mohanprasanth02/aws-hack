import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import '../config/theme.dart';
import '../models/work_order_model.dart';
import '../services/api_service.dart';

class PhotoCompletionScreen extends StatefulWidget {
  final WorkOrder task;

  const PhotoCompletionScreen({super.key, required this.task});

  @override
  State<PhotoCompletionScreen> createState() => _PhotoCompletionScreenState();
}

class _PhotoCompletionScreenState extends State<PhotoCompletionScreen> {
  Uint8List? _imageBytes;
  String? _imageFileName;
  final ImagePicker _picker = ImagePicker();

  final TextEditingController _findingsController = TextEditingController(
    text: 'Identified cracked isolation flange gasket causing continuous nocturnal departure.',
  );
  final TextEditingController _actionController = TextEditingController(
    text: 'Replaced with industrial EPDM seal, torqued to specification, re-pressurized to 3.2 bar with zero leakage verified.',
  );
  final TextEditingController _notesController = TextEditingController(
    text: 'Visual inspection passed; flow rate returned to nominal baseline.',
  );

  bool _isUploading = false;
  String? _uploadError;

  final List<Map<String, String>> _quickRemediations = [
    {
      'label': 'EPDM Gasket',
      'findings': 'Cracked isolation flange gasket causing sustained leakage under pressure.',
      'action': 'Replaced gasket with heavy-duty EPDM flange ring, torqued to 45 Nm.',
    },
    {
      'label': 'Valve Torqued',
      'findings': 'Loose gate valve gland packing nut allowing weepage along spindle.',
      'action': 'Tightened gland nuts, verified spindle seals, pressure tested to 3.5 bar.',
    },
    {
      'label': 'Union Replaced',
      'findings': 'Degraded brass compression union coupling showing hairline stress fracture.',
      'action': 'Cut damaged section, spliced with reinforced compression coupling.',
    },
    {
      'label': 'Meter Re-seated',
      'findings': 'Ultrasonic flow meter sensor housing misaligned, causing localized seep.',
      'action': 'Re-seated transducer clamp, reapplied acoustic gel, verified zero drift.',
    },
  ];

  @override
  void dispose() {
    _findingsController.dispose();
    _actionController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _capturePhoto(ImageSource source) async {
    HapticFeedback.selectionClick();
    try {
      final pickedFile = await _picker.pickImage(
        source: source,
        imageQuality: 85,
        maxWidth: 1600,
      );
      if (pickedFile != null) {
        final bytes = await pickedFile.readAsBytes();
        setState(() {
          _imageBytes = bytes;
          _imageFileName = pickedFile.name;
          _uploadError = null;
        });
      }
    } catch (e) {
      setState(() {
        _uploadError = 'Camera / file picker error: $e';
      });
    }
  }

  void _applyPreset(Map<String, String> preset) {
    HapticFeedback.selectionClick();
    setState(() {
      _findingsController.text = preset['findings']!;
      _actionController.text = preset['action']!;
    });
  }

  Future<void> _submitCompletion() async {
    HapticFeedback.mediumImpact();
    setState(() {
      _isUploading = true;
      _uploadError = null;
    });

    final success = await ApiService.completeTaskWithPhotoBytes(
      orderId: widget.task.id,
      photoBytes: _imageBytes,
      photoFileName: _imageFileName,
      findings: _findingsController.text.trim(),
      actionTaken: _actionController.text.trim(),
      notes: _notesController.text.trim(),
    );

    setState(() {
      _isUploading = false;
    });

    if (success) {
      if (!mounted) return;
      HapticFeedback.heavyImpact();
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          backgroundColor: AquaTheme.surfaceCard,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(22),
            side: BorderSide(color: AquaTheme.emeraldGreen.withOpacity(0.5)),
          ),
          title: const Row(
            children: [
              Icon(Icons.verified_rounded, color: AquaTheme.emeraldGreen, size: 28),
              SizedBox(width: 10),
              Text(
                'Remediation Verified',
                style: TextStyle(color: AquaTheme.platinumWhite, fontSize: 16, fontWeight: FontWeight.w800),
              ),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Work order ${widget.task.ticketId} has been resolved and synchronized with the central web console.',
                style: const TextStyle(color: AquaTheme.textMuted, fontSize: 13, height: 1.4),
              ),
              const SizedBox(height: 14),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AquaTheme.emeraldBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AquaTheme.emeraldGreen.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.eco_rounded, color: AquaTheme.emeraldGreen, size: 22),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Verified Savings: ~${(widget.task.estimatedLeakLph * 168).toStringAsFixed(0)} Liters conserved!',
                        style: const TextStyle(
                          color: AquaTheme.emeraldGreen,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          actions: [
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AquaTheme.iceCyan,
                foregroundColor: const Color(0xFF050607),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: () {
                Navigator.pop(context);
                Navigator.pop(context, true);
              },
              child: const Text('Return to Work Feed', style: TextStyle(fontWeight: FontWeight.w800)),
            ),
          ],
        ),
      );
    } else {
      HapticFeedback.heavyImpact();
      setState(() {
        _uploadError = 'Connection error. Please check server connection to ${ApiService.workerName}.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final estLph = widget.task.estimatedLeakLph > 0 ? widget.task.estimatedLeakLph : 140.0;
    final weeklyWaterSaved = estLph * 168; // 24 * 7
    final dollarSaved = (weeklyWaterSaved / 1000) * 2.50;

    return Scaffold(
      backgroundColor: AquaTheme.bgDark,
      appBar: AppBar(
        title: const Text('PHOTO PROOF & VERIFY'),
      ),
      body: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 540),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Ticket Header Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: AquaTheme.cardGradient,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: AquaTheme.borderLight),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.06),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            widget.task.ticketId,
                            style: const TextStyle(
                              fontFamily: 'monospace',
                              fontWeight: FontWeight.w800,
                              fontSize: 12.5,
                              color: AquaTheme.platinumWhite,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          widget.task.meterId,
                          style: const TextStyle(fontFamily: 'monospace', fontSize: 11, color: AquaTheme.textMuted),
                        ),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AquaTheme.solarAmberBg,
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: AquaTheme.solarAmber.withOpacity(0.5)),
                          ),
                          child: Text(
                            widget.task.priority.toUpperCase(),
                            style: const TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                              color: AquaTheme.solarAmber,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      widget.task.title,
                      style: const TextStyle(
                        fontSize: 14.5,
                        fontWeight: FontWeight.w800,
                        color: AquaTheme.platinumWhite,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.location_on_outlined, size: 13, color: AquaTheme.textMuted),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            widget.task.location,
                            style: const TextStyle(fontSize: 11.5, color: AquaTheme.textMuted),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // Camera Photo Capture Zone
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AquaTheme.surfaceCard,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(
                    color: _imageBytes != null ? AquaTheme.iceCyan.withOpacity(0.4) : AquaTheme.borderLight,
                    width: 1.2,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.camera_alt_rounded, size: 16, color: AquaTheme.iceCyan),
                        const SizedBox(width: 8),
                        const Text(
                          'PHYSICAL REMEDIATION PROOF',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.8,
                            color: AquaTheme.platinumWhite,
                          ),
                        ),
                        const Spacer(),
                        if (_imageBytes != null)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AquaTheme.emeraldBg,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: const Row(
                              children: [
                                Icon(Icons.check_circle_rounded, size: 12, color: AquaTheme.emeraldGreen),
                                SizedBox(width: 4),
                                Text(
                                  'PHOTO READY',
                                  style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.bold, color: AquaTheme.emeraldGreen),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Capture repaired pipe, sealed flange, or baseline meter display. Uploaded directly to central web audit gallery.',
                      style: TextStyle(fontSize: 11.5, color: AquaTheme.textMuted, height: 1.3),
                    ),
                    const SizedBox(height: 14),

                    // Preview / Drop Zone
                    Container(
                      height: 220,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: AquaTheme.surfaceInput,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                          color: _imageBytes != null ? AquaTheme.iceCyan.withOpacity(0.5) : Colors.white.withOpacity(0.1),
                          width: 1.0,
                        ),
                      ),
                      child: _imageBytes != null
                          ? ClipRRect(
                              borderRadius: BorderRadius.circular(14),
                              child: Stack(
                                fit: StackFit.expand,
                                children: [
                                  Image.memory(_imageBytes!, fit: BoxFit.cover),
                                  // Gradient Overlay
                                  Positioned(
                                    bottom: 0,
                                    left: 0,
                                    right: 0,
                                    child: Container(
                                      padding: const EdgeInsets.all(10),
                                      decoration: BoxDecoration(
                                        gradient: LinearGradient(
                                          colors: [Colors.transparent, Colors.black.withOpacity(0.8)],
                                          begin: Alignment.topCenter,
                                          end: Alignment.bottomCenter,
                                        ),
                                      ),
                                      child: Row(
                                        children: [
                                          const Icon(Icons.photo_size_select_actual_outlined, size: 14, color: Colors.white70),
                                          const SizedBox(width: 6),
                                          Expanded(
                                            child: Text(
                                              _imageFileName ?? 'remediation_proof.jpg',
                                              style: const TextStyle(color: Colors.white, fontSize: 11),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                          OutlinedButton.icon(
                                            onPressed: () => _capturePhoto(ImageSource.camera),
                                            icon: const Icon(Icons.replay_rounded, size: 13, color: AquaTheme.iceCyan),
                                            label: const Text('Retake', style: TextStyle(fontSize: 11, color: AquaTheme.iceCyan)),
                                            style: OutlinedButton.styleFrom(
                                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                              side: const BorderSide(color: AquaTheme.borderCyan),
                                              minimumSize: Size.zero,
                                              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                  // Remove Button
                                  Positioned(
                                    top: 10,
                                    right: 10,
                                    child: IconButton(
                                      icon: const Icon(Icons.close_rounded, color: Colors.white, size: 18),
                                      style: IconButton.styleFrom(
                                        backgroundColor: Colors.black.withOpacity(0.6),
                                        padding: const EdgeInsets.all(6),
                                        minimumSize: Size.zero,
                                      ),
                                      onPressed: () => setState(() {
                                        _imageBytes = null;
                                        _imageFileName = null;
                                      }),
                                    ),
                                  ),
                                ],
                              ),
                            )
                          : Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Container(
                                  width: 56,
                                  height: 56,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: Colors.white.withOpacity(0.04),
                                    border: Border.all(color: Colors.white.withOpacity(0.1)),
                                  ),
                                  child: const Center(
                                    child: Icon(Icons.add_a_photo_outlined, size: 26, color: AquaTheme.iceCyan),
                                  ),
                                ),
                                const SizedBox(height: 12),
                                const Text(
                                  'Tap below to take or choose photo proof',
                                  style: TextStyle(color: AquaTheme.textMuted, fontSize: 12.5),
                                ),
                                const SizedBox(height: 14),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    ElevatedButton.icon(
                                      onPressed: () => _capturePhoto(ImageSource.camera),
                                      icon: const Icon(Icons.photo_camera_rounded, size: 16),
                                      label: const Text('Camera', style: TextStyle(fontSize: 12)),
                                      style: ElevatedButton.styleFrom(
                                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                                      ),
                                    ),
                                    const SizedBox(width: 10),
                                    OutlinedButton.icon(
                                      onPressed: () => _capturePhoto(ImageSource.gallery),
                                      icon: const Icon(Icons.photo_library_rounded, size: 16),
                                      label: const Text('Gallery', style: TextStyle(fontSize: 12)),
                                      style: OutlinedButton.styleFrom(
                                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // Quick Remediation Presets (Crucial for mobile usability!)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'QUICK REMEDIATION PRESETS',
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.8,
                      color: AquaTheme.textMuted,
                    ),
                  ),
                  const SizedBox(height: 8),
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    physics: const BouncingScrollPhysics(),
                    child: Row(
                      children: _quickRemediations.map((preset) {
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: ActionChip(
                            avatar: const Icon(Icons.bolt_rounded, size: 14, color: AquaTheme.solarAmber),
                            label: Text(preset['label']!),
                            labelStyle: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700, color: AquaTheme.platinumWhite),
                            backgroundColor: AquaTheme.surfaceCard,
                            side: BorderSide(color: Colors.white.withOpacity(0.1)),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                            onPressed: () => _applyPreset(preset),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),

              // Technical Findings & Actions Form
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AquaTheme.surfaceCard,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: AquaTheme.borderLight),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'FIELD ACTION LOG',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.8,
                        color: AquaTheme.platinumWhite,
                      ),
                    ),
                    const SizedBox(height: 14),

                    TextField(
                      controller: _findingsController,
                      maxLines: 2,
                      style: const TextStyle(fontSize: 13, color: AquaTheme.platinumWhite),
                      decoration: const InputDecoration(
                        labelText: 'Root Cause Discovered',
                        prefixIcon: Icon(Icons.search_rounded, size: 18, color: AquaTheme.textMuted),
                      ),
                    ),
                    const SizedBox(height: 12),

                    TextField(
                      controller: _actionController,
                      maxLines: 2,
                      style: const TextStyle(fontSize: 13, color: AquaTheme.platinumWhite),
                      decoration: const InputDecoration(
                        labelText: 'Corrective Action Taken',
                        prefixIcon: Icon(Icons.build_rounded, size: 18, color: AquaTheme.textMuted),
                      ),
                    ),
                    const SizedBox(height: 12),

                    TextField(
                      controller: _notesController,
                      maxLines: 2,
                      style: const TextStyle(fontSize: 13, color: AquaTheme.platinumWhite),
                      decoration: const InputDecoration(
                        labelText: 'Follow-up Notes / Baseline Re-check',
                        prefixIcon: Icon(Icons.notes_rounded, size: 18, color: AquaTheme.textMuted),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // Water Recovery Impact Card
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AquaTheme.emeraldBg,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AquaTheme.emeraldGreen.withOpacity(0.35)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.eco_rounded, color: AquaTheme.emeraldGreen, size: 24),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'EXPECTED METRIC IMPACT',
                            style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800, color: AquaTheme.emeraldGreen, letterSpacing: 0.6),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '+${weeklyWaterSaved.toStringAsFixed(0)} L Conserved • \$${dollarSaved.toStringAsFixed(2)} Cost Avoided',
                            style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w800, color: AquaTheme.platinumWhite),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              if (_uploadError != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AquaTheme.criticalRedBg,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AquaTheme.criticalRed.withOpacity(0.4)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline_rounded, color: AquaTheme.criticalRed, size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _uploadError!,
                          style: const TextStyle(color: AquaTheme.criticalRed, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),
              ],

              // Full-Width Primary Submit Button
              Container(
                decoration: BoxDecoration(
                  gradient: AquaTheme.primaryGradient,
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [
                    BoxShadow(
                      color: AquaTheme.iceCyan.withOpacity(0.3),
                      blurRadius: 16,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: ElevatedButton(
                  onPressed: _isUploading ? null : _submitCompletion,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.transparent,
                    shadowColor: Colors.transparent,
                    foregroundColor: const Color(0xFF050607),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                  child: _isUploading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                        )
                      : const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.cloud_upload_rounded, size: 20),
                            SizedBox(width: 8),
                            Text(
                              'SUBMIT & SYNC WITH WEB CORE',
                              style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 0.6, fontSize: 13),
                            ),
                          ],
                        ),
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}

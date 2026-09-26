class WorkOrder {
  final int id;
  final String ticketId;
  final String meterId;
  final String location;
  final double latitude;
  final double longitude;
  final String title;
  final String priority;
  String status;
  final String assetType;
  final String assignedTechnician;
  final String assignedWorkerEmail;
  final double estimatedLeakLph;
  final String? photoUrl;
  final String? photoFilename;
  final String? actualFindings;
  final String? actionTaken;
  final String? completionNotes;
  final double waterSavedLiters;
  final double financialSavingsUsd;

  WorkOrder({
    required this.id,
    required this.ticketId,
    required this.meterId,
    required this.location,
    required this.latitude,
    required this.longitude,
    required this.title,
    required this.priority,
    required this.status,
    required this.assetType,
    required this.assignedTechnician,
    required this.assignedWorkerEmail,
    required this.estimatedLeakLph,
    this.photoUrl,
    this.photoFilename,
    this.actualFindings,
    this.actionTaken,
    this.completionNotes,
    this.waterSavedLiters = 0.0,
    this.financialSavingsUsd = 0.0,
  });

  factory WorkOrder.fromJson(Map<String, dynamic> json) {
    return WorkOrder(
      id: json['id'] ?? 0,
      ticketId: json['ticket_id'] ?? '',
      meterId: json['meter_id'] ?? '',
      location: json['location'] ?? 'SNS Kalvi Nagar, Coimbatore',
      latitude: (json['latitude'] != null) ? (json['latitude'] as num).toDouble() : 11.1018,
      longitude: (json['longitude'] != null) ? (json['longitude'] as num).toDouble() : 77.0275,
      title: json['title'] ?? 'Water Remediation',
      priority: json['priority'] ?? 'Medium',
      status: json['status'] ?? 'Dispatched',
      assetType: json['asset_type'] ?? 'Mains Pipeline',
      assignedTechnician: json['assigned_technician'] ?? 'Field Tech',
      assignedWorkerEmail: json['assigned_worker_email'] ?? 'worker@aquaguard.io',
      estimatedLeakLph: (json['estimated_leak_lph'] != null) ? (json['estimated_leak_lph'] as num).toDouble() : 120.0,
      photoUrl: json['photo_url'],
      photoFilename: json['photo_filename'],
      actualFindings: json['actual_findings'],
      actionTaken: json['action_taken'],
      completionNotes: json['completion_notes'],
      waterSavedLiters: (json['water_saved_liters'] != null) ? (json['water_saved_liters'] as num).toDouble() : 0.0,
      financialSavingsUsd: (json['financial_savings_usd'] != null) ? (json['financial_savings_usd'] as num).toDouble() : 0.0,
    );
  }
}

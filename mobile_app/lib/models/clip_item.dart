class ClipItem {
  final int? id;
  final String jobId;
  final String title;
  final double duration;
  final double start;
  final double end;
  final String streamUrl;
  final String downloadUrl;
  final String subtitleStyle;
  final String reason;
  final int viralScore;
  final String viralLabel;
  final String hookReason;
  final int createdAt;

  ClipItem({
    this.id,
    required this.jobId,
    required this.title,
    required this.duration,
    required this.start,
    required this.end,
    required this.streamUrl,
    required this.downloadUrl,
    required this.subtitleStyle,
    required this.reason,
    this.viralScore = 95,
    this.viralLabel = "Viral Sensation 🔥",
    this.hookReason = "High-retention opening hook with emotional punchline",
    required this.createdAt,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'job_id': jobId,
      'title': title,
      'duration': duration,
      'start_time': start,
      'end_time': end,
      'stream_url': streamUrl,
      'download_url': downloadUrl,
      'subtitle_style': subtitleStyle,
      'reason': reason,
      'viral_score': viralScore,
      'viral_label': viralLabel,
      'hook_reason': hookReason,
      'created_at': createdAt,
    };
  }

  factory ClipItem.fromMap(Map<String, dynamic> map) {
    return ClipItem(
      id: map['id'],
      jobId: map['job_id'] ?? '',
      title: map['title'] ?? 'Reel Clip',
      duration: (map['duration'] as num?)?.toDouble() ?? 0.0,
      start: (map['start_time'] as num?)?.toDouble() ?? 0.0,
      end: (map['end_time'] as num?)?.toDouble() ?? 0.0,
      streamUrl: map['stream_url'] ?? '',
      downloadUrl: map['download_url'] ?? '',
      subtitleStyle: map['subtitle_style'] ?? 'klap_kinetic',
      reason: map['reason'] ?? '',
      viralScore: (map['viral_score'] as num?)?.toInt() ?? 95,
      viralLabel: map['viral_label'] ?? 'Viral Sensation 🔥',
      hookReason: map['hook_reason'] ?? 'High engagement dialogue flow',
      createdAt: map['created_at'] ?? DateTime.now().millisecondsSinceEpoch,
    );
  }
}

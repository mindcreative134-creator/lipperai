import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:video_player/video_player.dart';
import '../models/clip_item.dart';

class ReelPlayerScreen extends StatefulWidget {
  final ClipItem clip;
  final String? videoId;

  const ReelPlayerScreen({super.key, required this.clip, this.videoId});

  @override
  State<ReelPlayerScreen> createState() => _ReelPlayerScreenState();
}

class _ReelPlayerScreenState extends State<ReelPlayerScreen> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  Timer? _playbackTimer;
  double _currentSeconds = 0.0;
  bool _isPlaying = true;
  int _activeWordIndex = 0;

  VideoPlayerController? _videoPlayerController;
  bool _isVideoInitialized = false;
  bool _hasVideoError = false;

  late List<String> _sampleWords;

  // Klap emoji dictionary
  final Map<String, String> _emojiMap = {
    "money": "💰", "cash": "💵", "rich": "🤑", "paisa": "💰",
    "crazy": "🤯", "shock": "😱", "shocking": "😱", "insane": "🤯",
    "fire": "🔥", "viral": "🚀", "secret": "🤫", "hack": "🔑",
    "laugh": "😂", "funny": "😂", "joke": "🤣", "stop": "🛑",
    "win": "🏆", "best": "🥇", "love": "❤️", "ai": "🤖"
  };

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 200),
      lowerBound: 1.0,
      upperBound: 1.30,
    );

    final dialogue = widget.clip.reason.isNotEmpty
        ? widget.clip.reason
        : "WAIT FOR IT... THIS IS THE CRAZIEST PART OF THE ENTIRE VIDEO!";
    final rawWords = dialogue.replaceAll(RegExp(r'[^\w\s\u0900-\u097F]'), '').split(' ');
    
    // Add emojis to key words
    _sampleWords = rawWords.map((w) {
      final clean = w.toLowerCase().trim();
      if (_emojiMap.containsKey(clean)) {
        return "$w ${_emojiMap[clean]}";
      }
      return w;
    }).toList();

    if (_sampleWords.isEmpty) {
      _sampleWords = ["WAIT", "FOR ⏳", "IT 🔥", "VIRAL 🚀", "REEL", "MOMENT 🤯"];
    }

    _initializeVideoIfPossible();
    _startSubtitleTicker();
  }

  void _initializeVideoIfPossible() {
    final streamUrl = widget.clip.streamUrl.trim();
    final isDirectVideo = streamUrl.endsWith(".mp4") ||
        streamUrl.contains("/stream/") ||
        streamUrl.contains("googlevideo.com") ||
        streamUrl.contains(".m3u8");

    if (isDirectVideo) {
      try {
        _videoPlayerController = VideoPlayerController.networkUrl(
          Uri.parse(streamUrl),
          httpHeaders: {"Bypass-Tunnel-Reminder": "true"},
        )..initialize().then((_) {
            if (mounted) {
              setState(() {
                _isVideoInitialized = true;
              });
              _videoPlayerController!.setLooping(true);
              _videoPlayerController!.play();
            }
          }).catchError((err) {
            if (mounted) {
              setState(() {
                _hasVideoError = true;
              });
            }
          });

        _videoPlayerController?.addListener(() {
          if (mounted && _videoPlayerController != null && _videoPlayerController!.value.isInitialized) {
            setState(() {
              _currentSeconds = _videoPlayerController!.value.position.inMilliseconds / 1000.0;
              _isPlaying = _videoPlayerController!.value.isPlaying;
            });
          }
        });
      } catch (e) {
        _hasVideoError = true;
      }
    }
  }

  void _startSubtitleTicker() {
    _playbackTimer?.cancel();
    _playbackTimer = Timer.periodic(const Duration(milliseconds: 340), (timer) {
      if (!_isPlaying) return;
      if (!mounted) return;
      setState(() {
        if (!_isVideoInitialized) {
          _currentSeconds += 0.34;
          if (_currentSeconds >= widget.clip.duration && widget.clip.duration > 0) {
            _currentSeconds = 0.0;
          }
        }
        _activeWordIndex = (_activeWordIndex + 1) % _sampleWords.length;
        _pulseController.forward(from: 1.0);
      });
    });
  }

  void _togglePlayPause() {
    if (_videoPlayerController != null && _videoPlayerController!.value.isInitialized) {
      setState(() {
        if (_videoPlayerController!.value.isPlaying) {
          _videoPlayerController!.pause();
          _isPlaying = false;
        } else {
          _videoPlayerController!.play();
          _isPlaying = true;
        }
      });
    } else {
      setState(() {
        _isPlaying = !_isPlaying;
      });
    }
  }

  Future<void> _openYouTubeAtTimestamp() async {
    final vId = widget.videoId ?? _extractVideoId(widget.clip.streamUrl);
    final startSec = widget.clip.start.toInt();
    
    // First try native YouTube app intent
    if (vId.isNotEmpty) {
      final appUri = Uri.parse("vnd.youtube:$vId?t=${startSec}s");
      try {
        if (await canLaunchUrl(appUri)) {
          await launchUrl(appUri);
          return;
        }
      } catch (_) {}
    }

    final webUrl = (vId.isNotEmpty)
        ? "https://www.youtube.com/watch?v=$vId&t=${startSec}s"
        : widget.clip.streamUrl;

    if (webUrl.isNotEmpty) {
      final uri = Uri.parse(webUrl);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
    }
  }

  String _extractVideoId(String url) {
    final reg = RegExp(r'(?:v=|\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})');
    final match = reg.firstMatch(url);
    return match?.group(1) ?? "";
  }

  @override
  void dispose() {
    _playbackTimer?.cancel();
    _pulseController.dispose();
    _videoPlayerController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final vId = widget.videoId ?? _extractVideoId(widget.clip.streamUrl);
    final thumbUrl = vId.isNotEmpty
        ? "https://i.ytimg.com/vi/$vId/hqdefault.jpg"
        : "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80";

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Background Blurred Image (9:16 Reel look)
          Positioned.fill(
            child: Image.network(
              thumbUrl,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Container(color: const Color(0xFF0F172A)),
            ),
          ),
          Positioned.fill(
            child: Container(
              color: Colors.black.withOpacity(0.72),
            ),
          ),

          // Central 9:16 Video Canvas
          Center(
            child: AspectRatio(
              aspectRatio: 9 / 16,
              child: GestureDetector(
                onTap: _togglePlayPause,
                child: Container(
                  decoration: BoxDecoration(
                    border: Border.all(color: const Color(0xFFFACC15).withOpacity(0.6), width: 1.5),
                    borderRadius: BorderRadius.circular(22),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFFFACC15).withOpacity(0.2),
                        blurRadius: 28,
                        spreadRadius: 2,
                      )
                    ],
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Stack(
                    children: [
                      // Video Player (If MP4 stream initialized) or Thumbnail
                      if (_isVideoInitialized && _videoPlayerController != null)
                        Positioned.fill(
                          child: FittedBox(
                            fit: BoxFit.cover,
                            child: SizedBox(
                              width: _videoPlayerController!.value.size.width,
                              height: _videoPlayerController!.value.size.height,
                              child: VideoPlayer(_videoPlayerController!),
                            ),
                          ),
                        )
                      else
                        Positioned.fill(
                          child: Image.network(
                            thumbUrl,
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => const Center(
                              child: Icon(Icons.movie, size: 80, color: Colors.white24),
                            ),
                          ),
                        ),

                      // Gradient Overlay top & bottom
                      Positioned.fill(
                        child: Container(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [
                                Colors.black.withOpacity(0.70),
                                Colors.transparent,
                                Colors.transparent,
                                Colors.black.withOpacity(0.90),
                              ],
                              stops: const [0.0, 0.20, 0.65, 1.0],
                            ),
                          ),
                        ),
                      ),

                      // TOP HUD: KLAP VIRAL SCORE METER
                      Positioned(
                        top: 16,
                        right: 16,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.75),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: const Color(0xFF10B981), width: 1.5),
                            boxShadow: [
                              BoxShadow(color: const Color(0xFF10B981).withOpacity(0.3), blurRadius: 10)
                            ],
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.local_fire_department, color: Color(0xFFFACC15), size: 16),
                              const SizedBox(width: 4),
                              Text(
                                "${widget.clip.viralScore}/100",
                                style: const TextStyle(color: Color(0xFF10B981), fontWeight: FontWeight.bold, fontSize: 13),
                              ),
                            ],
                          ),
                        ),
                      ),

                      // Play / Pause Indicator
                      if (!_isPlaying)
                        Center(
                          child: Container(
                            padding: const EdgeInsets.all(18),
                            decoration: BoxDecoration(
                              color: Colors.black.withOpacity(0.65),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.play_arrow, size: 48, color: Colors.white),
                          ),
                        ),

                      // LIVE KLAP KINETIC ANIMATED SUBTITLES (Shown when video doesn't already have burned-in subs)
                      if (!_isVideoInitialized)
                        Positioned(
                          bottom: 125,
                          left: 18,
                          right: 18,
                          child: _buildAnimatedSubtitleWidget(),
                        ),

                      // Bottom Info Bar inside Reel
                      Positioned(
                        bottom: 20,
                        left: 16,
                        right: 16,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.clip.title,
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                                shadows: [Shadow(color: Colors.black, blurRadius: 4)],
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 6),
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFFACC15),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    "${widget.clip.duration.toInt()}s Reel",
                                    style: const TextStyle(color: Color(0xFF0F1117), fontSize: 11, fontWeight: FontWeight.bold),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    widget.clip.viralLabel,
                                    style: const TextStyle(color: Colors.white70, fontSize: 12),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 10),
                            // Progress bar
                            LinearProgressIndicator(
                              value: widget.clip.duration > 0
                                  ? (_currentSeconds / widget.clip.duration).clamp(0.0, 1.0)
                                  : 0.5,
                              backgroundColor: Colors.white24,
                              valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFFFACC15)),
                              minHeight: 4,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // Top Header (Close button + Title)
          Positioned(
            top: 40,
            left: 16,
            right: 16,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back_ios, color: Colors.white),
                  onPressed: () => Navigator.pop(context),
                ),
                const Text(
                  "Klap AI Reel Player",
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                ),
                IconButton(
                  icon: const Icon(Icons.copy_rounded, color: Colors.white),
                  tooltip: "Copy dialogue text",
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: widget.clip.reason));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Dialogue copied to clipboard!")),
                    );
                  },
                ),
              ],
            ),
          ),

          // Floating Action Button at Bottom
          Positioned(
            bottom: 24,
            left: 24,
            right: 24,
            child: SizedBox(
              height: 52,
              child: ElevatedButton.icon(
                onPressed: _openYouTubeAtTimestamp,
                icon: const Icon(Icons.play_circle_fill, color: Colors.white, size: 24),
                label: Text(
                  "Watch on YouTube (${widget.clip.start.toInt()}s)",
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFFF0000),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  elevation: 8,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAnimatedSubtitleWidget() {
    final style = widget.clip.subtitleStyle.toLowerCase();

    final prevWord = _activeWordIndex > 0 ? _sampleWords[_activeWordIndex - 1] : "";
    final currentWord = _sampleWords[_activeWordIndex];
    final nextWord = _activeWordIndex + 1 < _sampleWords.length ? _sampleWords[_activeWordIndex + 1] : "";

    Color activeColor = const Color(0xFFFACC15); // Klap / Hormozi Yellow
    Color boxColor = Colors.transparent;
    double fontSize = 23.0;

    if (style.contains("neon") || style.contains("cyan")) {
      activeColor = const Color(0xFF00E5FF);
    } else if (style.contains("clean") || style.contains("white")) {
      activeColor = Colors.white;
    } else if (style.contains("box") || style.contains("red")) {
      activeColor = Colors.white;
      boxColor = Colors.redAccent.withOpacity(0.9);
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: boxColor != Colors.transparent ? boxColor : Colors.black.withOpacity(0.60),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: activeColor.withOpacity(0.45),
          width: 1.5,
        ),
      ),
      child: Center(
        child: Wrap(
          alignment: WrapAlignment.center,
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 8,
          children: [
            if (prevWord.isNotEmpty)
              Text(
                prevWord.toUpperCase(),
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  shadows: [Shadow(color: Colors.black, blurRadius: 4)],
                ),
              ),
            ScaleTransition(
              scale: _pulseController,
              child: Text(
                currentWord.toUpperCase(),
                style: TextStyle(
                  color: activeColor,
                  fontSize: fontSize,
                  fontWeight: FontWeight.w900,
                  shadows: [
                    Shadow(color: activeColor.withOpacity(0.6), blurRadius: 12),
                    const Shadow(color: Colors.black, blurRadius: 6),
                  ],
                ),
              ),
            ),
            if (nextWord.isNotEmpty)
              Text(
                nextWord.toUpperCase(),
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  shadows: [Shadow(color: Colors.black, blurRadius: 4)],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

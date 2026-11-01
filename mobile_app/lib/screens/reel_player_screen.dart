import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
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

  late List<String> _sampleWords;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 220),
      lowerBound: 1.0,
      upperBound: 1.25,
    );

    // Dialogue words for the animated captions
    final dialogue = widget.clip.reason.isNotEmpty
        ? widget.clip.reason
        : "WAIT FOR IT... THIS IS THE CRAZIEST PART OF THE ENTIRE VIDEO!";
    _sampleWords = dialogue.replaceAll(RegExp(r'[^\w\s\u0900-\u097F]'), '').split(' ');
    if (_sampleWords.isEmpty) {
      _sampleWords = ["WAIT", "FOR", "IT", "VIRAL", "REEL", "MOMENT"];
    }

    _startPlayback();
  }

  void _startPlayback() {
    _playbackTimer?.cancel();
    _playbackTimer = Timer.periodic(const Duration(milliseconds: 350), (timer) {
      if (!_isPlaying) return;
      setState(() {
        _currentSeconds += 0.35;
        if (_currentSeconds >= widget.clip.duration && widget.clip.duration > 0) {
          _currentSeconds = 0.0;
        }
        _activeWordIndex = (_activeWordIndex + 1) % _sampleWords.length;
        _pulseController.forward(from: 1.0);
      });
    });
  }

  void _togglePlayPause() {
    setState(() {
      _isPlaying = !_isPlaying;
    });
  }

  Future<void> _openYouTubeAtTimestamp() async {
    final vId = widget.videoId ?? _extractVideoId(widget.clip.streamUrl);
    final startSec = widget.clip.start.toInt();
    final url = (vId.isNotEmpty)
        ? "https://www.youtube.com/watch?v=$vId&t=${startSec}s"
        : widget.clip.streamUrl;

    if (url.isNotEmpty) {
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
    }
  }

  String _extractVideoId(String url) {
    final reg = RegExp(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*');
    final match = reg.firstMatch(url);
    return match?.group(1) ?? "";
  }

  @override
  void dispose() {
    _playbackTimer?.cancel();
    _pulseController.dispose();
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
              color: Colors.black.withOpacity(0.65),
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
                    border: Border.all(color: const Color(0xFF6366F1).withOpacity(0.5), width: 1.5),
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF6366F1).withOpacity(0.25),
                        blurRadius: 25,
                        spreadRadius: 2,
                      )
                    ],
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Stack(
                    children: [
                      // Video Thumbnail in center
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
                                Colors.black.withOpacity(0.7),
                                Colors.transparent,
                                Colors.transparent,
                                Colors.black.withOpacity(0.85),
                              ],
                              stops: const [0.0, 0.2, 0.7, 1.0],
                            ),
                          ),
                        ),
                      ),

                      // Play / Pause Indicator
                      if (!_isPlaying)
                        Center(
                          child: Container(
                            padding: const EdgeInsets.all(18),
                            decoration: BoxDecoration(
                              color: Colors.black.withOpacity(0.6),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.play_arrow, size: 48, color: Colors.white),
                          ),
                        ),

                      // LIVE WORD-BY-WORD ANIMATED SUBTITLES
                      Positioned(
                        bottom: 120,
                        left: 20,
                        right: 20,
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
                                fontSize: 16,
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
                                    color: const Color(0xFF6366F1),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    "${widget.clip.duration.toInt()}s Reel",
                                    style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  "Start: ${widget.clip.start.toInt()}s • Style: ${widget.clip.subtitleStyle}",
                                  style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12),
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
                              valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF6366F1)),
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
                  "9:16 Viral Reel Player",
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
                  "Open on YouTube (${widget.clip.start.toInt()}s)",
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.redAccent,
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

    // Show 3 words at a time: previous, active, next
    final prevWord = _activeWordIndex > 0 ? _sampleWords[_activeWordIndex - 1] : "";
    final currentWord = _sampleWords[_activeWordIndex];
    final nextWord = _activeWordIndex + 1 < _sampleWords.length ? _sampleWords[_activeWordIndex + 1] : "";

    Color activeColor;
    Color boxColor = Colors.transparent;
    double fontSize = 24.0;
    FontWeight fontWeight = FontWeight.w900;

    if (style.contains("hormozi")) {
      // Alex Hormozi Vibrant Yellow
      activeColor = const Color(0xFFFFEB3B);
    } else if (style.contains("neon") || style.contains("cyan")) {
      // Cyber Neon Cyan
      activeColor = const Color(0xFF00E5FF);
    } else if (style.contains("box") || style.contains("red")) {
      // Breaking Box Red
      activeColor = Colors.white;
      boxColor = Colors.redAccent.withOpacity(0.9);
    } else {
      // Clean White
      activeColor = Colors.white;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: boxColor != Colors.transparent ? boxColor : Colors.black.withOpacity(0.55),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: activeColor.withOpacity(0.4),
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
                  fontSize: 18,
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
                  fontWeight: fontWeight,
                  shadows: [
                    Shadow(color: activeColor.withOpacity(0.6), blurRadius: 10),
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
                  fontSize: 18,
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


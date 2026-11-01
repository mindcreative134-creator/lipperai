import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../database/db_helper.dart';
import '../models/clip_item.dart';
import 'reel_player_screen.dart';

class SavedClipsScreen extends StatefulWidget {
  final String serverUrl;
  const SavedClipsScreen({super.key, required this.serverUrl});

  @override
  State<SavedClipsScreen> createState() => _SavedClipsScreenState();
}

class _SavedClipsScreenState extends State<SavedClipsScreen> {
  List<ClipItem> _savedClips = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadClipsFromDb();
  }

  Future<void> _loadClipsFromDb() async {
    setState(() => _isLoading = true);
    final clips = await DatabaseHelper.instance.getAllClips();
    setState(() {
      _savedClips = clips;
      _isLoading = false;
    });
  }

  Future<void> _deleteClip(int id) async {
    await DatabaseHelper.instance.deleteClip(id);
    _loadClipsFromDb();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Clip removed from local SQLite database")),
      );
    }
  }

  String _extractVideoId(String url) {
    final reg = RegExp(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*');
    final match = reg.firstMatch(url);
    return match?.group(1) ?? "";
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B0F19),
      appBar: AppBar(
        backgroundColor: const Color(0xFF111827),
        elevation: 0,
        title: const Text("My Saved Reels (SQLite)", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 17)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadClipsFromDb,
            tooltip: "Refresh from SQLite",
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF6366F1)))
          : _savedClips.isEmpty
              ? _buildEmptyState()
              : _buildClipsList(),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.video_library_outlined, size: 64, color: Colors.grey.shade600),
          const SizedBox(height: 16),
          const Text("No Clips Saved Yet", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 8),
          Text(
            "Generate reels from YouTube links,\nand they will be saved here in SQLite automatically!",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey.shade400, fontSize: 13),
          ),
        ],
      ),
    );
  }

  Widget _buildClipsList() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _savedClips.length,
      itemBuilder: (context, index) {
        final clip = _savedClips[index];
        final vId = _extractVideoId(clip.streamUrl);
        final thumbUrl = vId.isNotEmpty
            ? "https://i.ytimg.com/vi/$vId/hqdefault.jpg"
            : "";

        return Card(
          margin: const EdgeInsets.only(bottom: 16),
          color: const Color(0xFF111827),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Color(0xFF1F2937)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: const Color(0xFF6366F1).withOpacity(0.2),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        "REEL #${index + 1} • ${clip.duration.toInt()}s",
                        style: const TextStyle(color: Color(0xFF818CF8), fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 20),
                      onPressed: () => _deleteClip(clip.id!),
                      tooltip: "Delete",
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // Thumbnail & Title Row
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (thumbUrl.isNotEmpty)
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.network(
                          thumbUrl,
                          width: 80,
                          height: 56,
                          fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => Container(
                            width: 80,
                            height: 56,
                            color: Colors.grey.shade800,
                            child: const Icon(Icons.movie, color: Colors.white38),
                          ),
                        ),
                      ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            clip.title,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            "Timestamp: ${clip.start.toInt()}s - ${clip.end.toInt()}s",
                            style: TextStyle(color: Colors.grey.shade400, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),

                if (clip.reason.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    clip.reason,
                    style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
                const SizedBox(height: 14),

                // Action Buttons
                Row(
                  children: [
                    // Watch Reel with Animated Subtitles
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => ReelPlayerScreen(clip: clip, videoId: vId),
                            ),
                          );
                        },
                        icon: const Icon(Icons.play_arrow_rounded, size: 20),
                        label: const Text("Watch Reel", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF6366F1),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    // Open YouTube directly
                    ElevatedButton(
                      onPressed: () async {
                        final startSec = clip.start.toInt();
                        final url = vId.isNotEmpty
                            ? "https://www.youtube.com/watch?v=$vId&t=${startSec}s"
                            : clip.streamUrl;
                        final uri = Uri.parse(url);
                        if (await canLaunchUrl(uri)) {
                          await launchUrl(uri, mode: LaunchMode.externalApplication);
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.redAccent.withOpacity(0.2),
                        foregroundColor: Colors.redAccent,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                      child: const Icon(Icons.open_in_new, size: 18),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

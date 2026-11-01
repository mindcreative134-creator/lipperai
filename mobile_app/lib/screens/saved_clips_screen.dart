import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../database/db_helper.dart';
import '../models/clip_item.dart';

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
                        style: const TextStyle(color: Color(0xFF818CF8), fontSize: 10, fontWeight: FontWeight.bold),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 20),
                      onPressed: () => _deleteClip(clip.id!),
                      tooltip: "Delete",
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  clip.title,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                if (clip.reason.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    clip.reason,
                    style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  height: 44,
                  child: ElevatedButton.icon(
                    onPressed: () async {
                      final url = "${widget.serverUrl}${clip.downloadUrl}";
                      final uri = Uri.parse(url);
                      if (await canLaunchUrl(uri)) {
                        await launchUrl(uri, mode: LaunchMode.externalApplication);
                      }
                    },
                    icon: const Icon(Icons.download_rounded, size: 18),
                    label: const Text("Download to Phone Gallery", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF6366F1),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}


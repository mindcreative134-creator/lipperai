import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';
import 'database/db_helper.dart';
import 'models/clip_item.dart';
import 'widgets/app_logo.dart';
import 'screens/saved_clips_screen.dart';

// Change this to your public server URL (or http://10.0.2.2:5000 for Android emulator)
const String SERVER_URL = "http://10.0.2.2:5000";

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ClipperAiApp());
}

class ClipperAiApp extends StatelessWidget {
  const ClipperAiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ClipperAI - Viral Reel Maker',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0B0F19),
        primaryColor: const Color(0xFF6366F1),
        cardColor: const Color(0xFF111827),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF6366F1),
          secondary: Color(0xFFEC4899),
        ),
      ),
      home: const MainNavigationScreen(),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  final List<Widget> _pages = [
    const GeneratorScreen(serverUrl: SERVER_URL),
    const SavedClipsScreen(serverUrl: SERVER_URL),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_currentIndex],
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: Color(0xFF1F2937), width: 1)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          backgroundColor: const Color(0xFF111827),
          selectedItemColor: const Color(0xFF818CF8),
          unselectedItemColor: Colors.grey.shade600,
          onTap: (index) => setState(() => _currentIndex = index),
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.auto_awesome),
              label: "Create Reels",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.storage_rounded),
              label: "Saved in SQLite",
            ),
          ],
        ),
      ),
    );
  }
}

class GeneratorScreen extends StatefulWidget {
  final String serverUrl;
  const GeneratorScreen({super.key, required this.serverUrl});

  @override
  State<GeneratorScreen> createState() => _GeneratorScreenState();
}

class _GeneratorScreenState extends State<GeneratorScreen> {
  final TextEditingController _urlController = TextEditingController();
  final TextEditingController _keywordController = TextEditingController();

  String _selectedMode = "auto";
  String _selectedTemplate = "hormozi";
  bool _isLoading = false;
  double _progress = 0.0;
  String _stepMessage = "";
  List<ClipItem> _newClips = [];
  Timer? _pollTimer;

  Future<void> _startClipping() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please enter a YouTube video URL")),
      );
      return;
    }

    setState(() {
      _isLoading = true;
      _progress = 0.05;
      _stepMessage = "Connecting to server...";
      _newClips = [];
    });

    try {
      final res = await http.post(
        Uri.parse("${widget.serverUrl}/api/jobs/create"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "url": url,
          "mode": _selectedMode,
          "search_query": _keywordController.text.trim(),
          "subtitle_template": _selectedTemplate,
          "format": "9:16",
          "max_clips": 3,
        }),
      );

      final data = jsonDecode(res.body);
      if (data["success"] == true) {
        final jobId = data["job_id"];
        _pollJobStatus(jobId);
      } else {
        _showError(data["error"] ?? "Failed to create job");
      }
    } catch (e) {
      _showError("Server connection error: $e");
    }
  }

  void _pollJobStatus(String jobId) {
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      try {
        final res = await http.get(Uri.parse("${widget.serverUrl}/api/jobs/$jobId"));
        final job = jsonDecode(res.body);

        setState(() {
          _progress = (job["progress"] ?? 0) / 100.0;
          _stepMessage = job["step_message"] ?? "Processing...";
        });

        if (job["status"] == "completed") {
          timer.cancel();
          final rawClips = job["clips"] as List<dynamic>? ?? [];
          List<ClipItem> savedList = [];

          // Save each clip directly into phone's SQLite Database!
          for (var c in rawClips) {
            final item = ClipItem(
              jobId: jobId,
              title: c["title"] ?? "Viral Reel",
              duration: (c["duration"] as num?)?.toDouble() ?? 0.0,
              start: (c["start"] as num?)?.toDouble() ?? 0.0,
              end: (c["end"] as num?)?.toDouble() ?? 0.0,
              streamUrl: c["stream_url"] ?? "",
              downloadUrl: c["download_url"] ?? "",
              subtitleStyle: _selectedTemplate,
              reason: c["reason"] ?? "",
              createdAt: DateTime.now().millisecondsSinceEpoch,
            );
            await DatabaseHelper.instance.insertClip(item);
            savedList.add(item);
          }

          setState(() {
            _isLoading = false;
            _newClips = savedList;
          });

          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text("Success! Clips generated & saved to phone SQLite!"),
                backgroundColor: Colors.green,
              ),
            );
          }
        } else if (job["status"] == "failed") {
          timer.cancel();
          _showError(job["error"] ?? "Video processing failed");
        }
      } catch (e) {
        timer.cancel();
        _showError("Error checking progress: $e");
      }
    });
  }

  void _showError(String message) {
    setState(() => _isLoading = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.redAccent),
    );
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _urlController.dispose();
    _keywordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF111827),
        elevation: 0,
        title: Row(
          children: const [
            AppLogo(size: 32),
            SizedBox(width: 10),
            Text("ClipperAI", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          ],
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_isLoading) _buildProgressCard(),
            if (!_isLoading && _newClips.isEmpty) _buildInputCard(),
            if (_newClips.isNotEmpty) _buildResultsFeed(),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressCard() {
    return Card(
      color: const Color(0xFF111827),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: Color(0xFF6366F1), width: 1)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("Generating Viral Reels...", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                Text("${(_progress * 100).toInt()}%", style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF818CF8))),
              ],
            ),
            const SizedBox(height: 14),
            LinearProgressIndicator(
              value: _progress,
              backgroundColor: const Color(0xFF1F2937),
              color: const Color(0xFF6366F1),
              minHeight: 8,
              borderRadius: BorderRadius.circular(4),
            ),
            const SizedBox(height: 12),
            Text(_stepMessage, style: TextStyle(color: Colors.grey.shade400, fontSize: 13), textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }

  Widget _buildInputCard() {
    return Card(
      color: const Color(0xFF111827),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text("YOUTUBE VIDEO LINK", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
            const SizedBox(height: 8),
            TextField(
              controller: _urlController,
              decoration: InputDecoration(
                hintText: "https://youtu.be/...",
                prefixIcon: const Icon(Icons.play_circle_fill, color: Colors.redAccent),
                filled: true,
                fillColor: const Color(0xFF1F2937),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
              ),
            ),
            const SizedBox(height: 18),

            const Text("CUTTING MODE", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _selectedMode,
              dropdownColor: const Color(0xFF1F2937),
              decoration: InputDecoration(
                filled: true,
                fillColor: const Color(0xFF1F2937),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
              ),
              items: const [
                DropdownMenuItem(value: "auto", child: Text("🤖 Smart Multi-Modal (Complete Sentences)")),
                DropdownMenuItem(value: "keyword", child: Text("🔍 Topic / Word Search")),
                DropdownMenuItem(value: "splitter", child: Text("✂️ 60s Consecutive Reel Splitter")),
              ],
              onChanged: (val) => setState(() => _selectedMode = val!),
            ),
            const SizedBox(height: 18),

            const Text("SUBTITLE TEMPLATE", style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildTemplateChip("hormozi", "🟡 Viral Hormozi"),
                _buildTemplateChip("clean_white", "⚪ Clean Minimal"),
                _buildTemplateChip("neon_cyan", "🟢 Neon Cyber"),
                _buildTemplateChip("red_box", "🔴 Breaking Box"),
              ],
            ),
            const SizedBox(height: 24),

            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton.icon(
                onPressed: _startClipping,
                icon: const Icon(Icons.auto_awesome),
                label: const Text("Generate Reels With AI", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF6366F1),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTemplateChip(String key, String label) {
    final isSelected = _selectedTemplate == key;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      selectedColor: const Color(0xFF6366F1).withOpacity(0.3),
      backgroundColor: const Color(0xFF1F2937),
      labelStyle: TextStyle(
        color: isSelected ? Colors.white : Colors.grey,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
      ),
      onSelected: (selected) {
        if (selected) setState(() => _selectedTemplate = key);
      },
    );
  }

  Widget _buildResultsFeed() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text("GENERATED REELS (SAVED IN SQLITE)", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            TextButton(
              onPressed: () => setState(() => _newClips = []),
              child: const Text("Create Another"),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ..._newClips.map((clip) => Card(
          margin: const EdgeInsets.only(bottom: 16),
          color: const Color(0xFF111827),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(clip.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white)),
                Text("${clip.duration.toInt()}s • Complete thought dialogue", style: TextStyle(color: Colors.grey.shade400, fontSize: 12)),
                const SizedBox(height: 14),
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
                    icon: const Icon(Icons.download, size: 18),
                    label: const Text("Save to Phone Gallery"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFEC4899),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                ),
              ],
            ),
          ),
        )),
      ],
    );
  }
}

import 'dart:async';
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';
import '../models/clip_item.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('clipper_ai.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 2,
      onCreate: _createDB,
      onUpgrade: _onUpgrade,
    );
  }

  Future _createDB(Database db, int version) async {
    await db.execute('''
      CREATE TABLE clips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        title TEXT NOT NULL,
        duration REAL NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        stream_url TEXT NOT NULL,
        download_url TEXT NOT NULL,
        subtitle_style TEXT NOT NULL,
        reason TEXT,
        viral_score INTEGER DEFAULT 95,
        viral_label TEXT DEFAULT 'Viral Sensation 🔥',
        hook_reason TEXT,
        created_at INTEGER NOT NULL
      )
    ''');
  }

  Future _onUpgrade(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      try {
        await db.execute("ALTER TABLE clips ADD COLUMN viral_score INTEGER DEFAULT 95");
        await db.execute("ALTER TABLE clips ADD COLUMN viral_label TEXT DEFAULT 'Viral Sensation 🔥'");
        await db.execute("ALTER TABLE clips ADD COLUMN hook_reason TEXT");
      } catch (_) {}
    }
  }

  Future<int> insertClip(ClipItem clip) async {
    final db = await instance.database;
    return await db.insert('clips', clip.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<List<ClipItem>> getAllClips() async {
    final db = await instance.database;
    final result = await db.query('clips', orderBy: 'created_at DESC');
    return result.map((json) => ClipItem.fromMap(json)).toList();
  }

  Future<int> deleteClip(int id) async {
    final db = await instance.database;
    return await db.delete('clips', where: 'id = ?', whereArgs: [id]);
  }

  Future<int> clearAllClips() async {
    final db = await instance.database;
    return await db.delete('clips');
  }

  Future close() async {
    final db = await instance.database;
    db.close();
  }
}

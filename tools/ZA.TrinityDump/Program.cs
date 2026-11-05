using System.Security.Cryptography;
using System.IO.Compression;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using Trinity.Core.Cache;
using Trinity.Core.Compression;
using Trinity.Core.Flatbuffers.TR.ResourceDictionary;
using Trinity.Core.Math.Hash;
using Trinity.Core.Serializers.TR;
using Trinity.Core.Utils;

namespace ZA.TrinityDump;

internal static class Program
{
    private static int Main(string[] args)
    {
        try
        {
            var options = ParseArgs(args);
            return options.ContainsKey("--descriptor-only") ? ExportDescriptorIndex(options) : Execute(options);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"FATAL: {ex}");
            return 2;
        }
    }

    private static Dictionary<string, string> ParseArgs(string[] args)
    {
        var options = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        for (int i = 0; i < args.Length; i++)
        {
            if (!args[i].StartsWith("--", StringComparison.Ordinal)) throw new ArgumentException("Expected --option: " + args[i]);
            if (args[i] is "--dry-run" or "--include-unused" or "--descriptor-only")
            {
                options[args[i]] = "true";
                continue;
            }
            if (i + 1 == args.Length) throw new ArgumentException("Missing value after " + args[i]);
            options[args[i]] = args[++i];
        }
        foreach (string required in new[] {"--romfs", "--output", "--cache"})
            if (!options.ContainsKey(required)) throw new ArgumentException("Missing " + required);
        return options;
    }

    private static string Sha256(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes));
    private static string Sha256File(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream));
    }

    private static int Limit(Dictionary<string, string> args, string name)
        => args.TryGetValue(name, out var value) ? int.Parse(value) : int.MaxValue;

    private sealed record ExportRow(
        string Status, string Hash, string Name, string? OutputPath, string? Sha256,
        long Size, string PackName, long PackOffset, string? Error);

    private static string? SafeRelativePath(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw) || Path.IsPathRooted(raw)) return null;
        var normalized = raw.Replace('\\', '/');
        if (normalized.StartsWith('/') || normalized.Contains(':')) return null;
        var parts = normalized.Split('/');
        if (parts.Any(p => p is "" or "." or ".." || p.EndsWith(' ') || p.EndsWith('.') ||
                           p.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0))
            return null;
        return string.Join('/', parts);
    }


    // M1: Read native data.trpfd directly; no data.trpfs restoration required.
    private static int ExportDescriptorIndex(Dictionary<string, string> args)
    {
        string romfs = Path.GetFullPath(args["--romfs"]);
        string descriptorPath = Path.Combine(romfs, "arc", "data.trpfd");
        string cachePath = Path.GetFullPath(args["--cache"]);
        string output = Path.GetFullPath(args["--output"]);
        if (!File.Exists(descriptorPath)) throw new FileNotFoundException("Missing data.trpfd", descriptorPath);
        if (!File.Exists(cachePath)) throw new FileNotFoundException("Missing GFPAKHashCache.bin", cachePath);
        if (output.StartsWith(romfs.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar,
                              StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("The index output must not modify the original RomFS.");
        var descriptor = FlatBufferConverter.DeserializeFrom<CustomFileDescriptor>(descriptorPath);
        if (descriptor is null) throw new InvalidDataException("TRPFD cannot be decoded");
        if (descriptor.FileHashes.Length != descriptor.FileInfo.Length ||
            descriptor.PackNames.Length != descriptor.PackInfo.Length)
            throw new InvalidDataException("TRPFD hash/pack information length mismatch.");
        if (descriptor.FileHashes.Length == 0 || descriptor.PackNames.Length == 0)
            throw new InvalidDataException("Empty TRPFD: refusing to publish misleading index.");

        GFPakHashCache.Open(cachePath);
        Directory.CreateDirectory(Path.Combine(output, "_index"));
        string hashListName = Path.Combine(output, "_index", "file_index.tsv.gz");
        string packListName = Path.Combine(output, "_index", "pack_index.tsv");
        var counts = new long[descriptor.PackNames.Length];
        long known = 0;
        // GZip output is deterministic; use a checked temporary path, then atomic move.
        var tempFile = hashListName + ".za-writing";
        using (var compressed = new GZipStream(new FileStream(tempFile, FileMode.CreateNew, FileAccess.Write),
                                               CompressionLevel.Optimal))
        using (var writer = new StreamWriter(compressed, new UTF8Encoding(false)))
        {
            writer.WriteLine("hash\tpack_index\tpack_name\tvirtual_path");
            for (int i = 0; i < descriptor.FileHashes.Length; i++)
            {
                ulong hash = descriptor.FileHashes[i];
                int index = checked((int)descriptor.FileInfo[i].PackIndex);
                if (index < 0 || index >= descriptor.PackNames.Length)
                    throw new InvalidDataException($"Pack index out of bounds at file record {i}: {index}");
                counts[index]++;
                var name = GFPakHashCache.GetName(hash);
                if (name is not null) known++;
                writer.Write(hash.ToString("X16"));
                writer.Write('\t');
                writer.Write(index);
                writer.Write('\t');
                writer.Write(descriptor.PackNames[index].Replace('\t', ' '));
                writer.Write('\t');
                writer.WriteLine(name?.Replace('\t', ' ').Replace('\n', ' ').Replace('\r', ' ') ?? "");
            }
        }
        File.Move(tempFile, hashListName, true);
        using (var writer = new StreamWriter(packListName, false, new UTF8Encoding(false)))
        {
            writer.WriteLine("pack_index\tpack_name\treferenced_files\tpacked_bytes\treported_file_count");
            for (int i = 0; i < descriptor.PackNames.Length; i++)
            {
                var p = descriptor.PackInfo[i];
                writer.WriteLine($"{i}\t{descriptor.PackNames[i].Replace('\t', ' ')}\t{counts[i]}\t{p.FileSize}\t{p.FileCount}");
            }
        }
        var unused = descriptor.UnusedHashes?.Length ?? 0;
        var summary = new
        {
            gameVersion = "v2.0.2",
            sourcePath = "v2.0.2/1/arc/data.trpfd",
            sourceBytes = new System.IO.FileInfo(descriptorPath).Length,
            sourceSha256 = Sha256File(descriptorPath),
            cacheSha256 = Sha256File(cachePath),
            hashCacheEntries = GFPakHashCache.Count,
            descriptorFiles = descriptor.FileHashes.Length,
            namedFiles = known,
            unnamedFiles = descriptor.FileHashes.Length - known,
            packCount = descriptor.PackNames.Length,
            unreferencedFiles = unused,
            compressedFileIndex = "_index/file_index.tsv.gz",
            packIndex = "_index/pack_index.tsv",
            evidence = "CONFIRMED_NATIVE_TRPFD",
            trpfsRestored = false,
            trpfsVirtualFilesExtracted = false
        };
        string summaryFile = Path.Combine(output, "_index", "descriptor_summary.json");
        File.WriteAllText(summaryFile, JsonSerializer.Serialize(summary,
            new JsonSerializerOptions { WriteIndented = true }) + "\n", new UTF8Encoding(false));
        Console.WriteLine($"TRPFD decoded: {summary.descriptorFiles} files / {summary.packCount} packs; known={known}, unknown={summary.unnamedFiles}");
        Console.WriteLine($"Wrote: {summaryFile}, {hashListName}, {packListName}");
        return 0;
    }

    private static int Execute(Dictionary<string, string> args)
    {
        string romfs = Path.GetFullPath(args["--romfs"]);
        string output = Path.GetFullPath(args["--output"]);
        string descriptorPath = Path.Combine(romfs, "arc", "data.trpfd");
        string trpfsPath = Path.Combine(romfs, "arc", "data.trpfs");
        string cachePath = Path.GetFullPath(args["--cache"]);
        bool dry = args.ContainsKey("--dry-run");
        if (!File.Exists(descriptorPath) || !File.Exists(trpfsPath) || !File.Exists(cachePath))
            throw new FileNotFoundException("Missing verified data.trpfd, data.trpfs, or GFPAKHashCache.bin");
        if (output.StartsWith(romfs.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar,
                              StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Output must not be inside the source RomFS.");
        GFPakHashCache.Open(cachePath);
        Console.WriteLine($"Hash cache: {GFPakHashCache.Count} names");

        var descriptor = FlatBufferConverter.DeserializeFrom<CustomFileDescriptor>(descriptorPath);
        var filesystem = ONEFILESerializer.DeserializeFileSystem(trpfsPath);
        if (descriptor is null || filesystem is null) throw new InvalidDataException("Invalid Trinity descriptor/filesystem");
        if (descriptor.FileHashes.Length != descriptor.FileInfo.Length)
            throw new InvalidDataException("TRPFD hash/info count mismatch");
        if (filesystem.FileHashes.Length != filesystem.FileOffsets.Length)
            throw new InvalidDataException("TRPFS hash/offset count mismatch");

        string? dll = args.GetValueOrDefault("--oodle");
        if (!dry && !string.IsNullOrWhiteSpace(dll))
        {
            dll = Path.GetFullPath(dll);
            if (!File.Exists(dll)) throw new FileNotFoundException("Oodle not found", dll);
            string absoluteDll = dll;
            NativeLibrary.SetDllImportResolver(typeof(Oodle).Assembly, (name, assembly, searchPath) =>
                name.Equals("oo2core_8_win64", StringComparison.OrdinalIgnoreCase)
                    ? NativeLibrary.Load(absoluteDll) : IntPtr.Zero);
        }

        var offsetByHash = new Dictionary<ulong, long>();
        for (int i = 0; i < filesystem.FileHashes.Length; i++)
            offsetByHash[filesystem.FileHashes[i]] = checked((long)filesystem.FileOffsets[i]);
        var grouped = new SortedDictionary<int, HashSet<ulong>>();
        for (int i = 0; i < descriptor.FileHashes.Length; i++)
        {
            int packIndex = checked((int)descriptor.FileInfo[i].PackIndex);
            if (!grouped.TryGetValue(packIndex, out var hashes))
                grouped[packIndex] = hashes = new HashSet<ulong>();
            hashes.Add(descriptor.FileHashes[i]);
        }
        if (args.ContainsKey("--include-unused") && descriptor.UnusedHashes is not null &&
            descriptor.UnusedFileInfo is not null)
        {
            int n = Math.Min(descriptor.UnusedHashes.Length, descriptor.UnusedFileInfo.Length);
            for (int i = 0; i < n; i++)
            {
                int packIndex = checked((int)descriptor.UnusedFileInfo[i].PackIndex);
                if (!grouped.TryGetValue(packIndex, out var hashes))
                    grouped[packIndex] = hashes = new HashSet<ulong>();
                hashes.Add(descriptor.UnusedHashes[i]);
            }
        }
        Console.WriteLine($"Trinity: {grouped.Count} referenced packs, {grouped.Sum(x => x.Value.Count)} hashes");
        if (dry) return 0;

        string outputVirtual = Path.Combine(output, "virtual");
        string indexDir = Path.Combine(output, "_index");
        Directory.CreateDirectory(indexDir);
        string reportPath = args.TryGetValue("--report", out var requestedReport)
            ? Path.GetFullPath(requestedReport) : Path.Combine(indexDir, "export.jsonl");
        string reportRoot = Path.GetFullPath(indexDir).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!Path.GetFullPath(reportPath).StartsWith(reportRoot, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Batch report must be stored inside the output _index directory");
        Directory.CreateDirectory(Path.GetDirectoryName(reportPath)!);
        var prior = new Dictionary<string, ExportRow>(StringComparer.Ordinal);
        if (File.Exists(reportPath))
            foreach (var line in File.ReadLines(reportPath))
            {
                try
                {
                    var row = JsonSerializer.Deserialize<ExportRow>(line);
                    if (row is not null) prior[row.Hash] = row;
                }
                catch (JsonException) { /* incomplete last record: retry */ }
            }

        using var log = new StreamWriter(new FileStream(reportPath, FileMode.Append, FileAccess.Write, FileShare.Read),
                                         new UTF8Encoding(false)) { AutoFlush = true };
        using var input = File.OpenRead(trpfsPath);
        int ok = 0, skipped = 0, failed = 0, examined = 0, packs = 0;
        int maxPacks = Limit(args, "--max-packs"), maxFiles = Limit(args, "--max-files");
        int startPack = args.TryGetValue("--start-pack", out var rawStartPack) ? int.Parse(rawStartPack) : 0;
        if (startPack < 0 || maxPacks <= 0 || maxFiles <= 0) throw new ArgumentException("Invalid pack/file window");
        int packCursor = 0;
        foreach (var group in grouped)
        {
            if (packCursor++ < startPack) continue;
            if (packs >= maxPacks || examined >= maxFiles) break;
            packs++;
            int packIndex = group.Key;
            string packName = packIndex >= 0 && packIndex < descriptor.PackNames.Length ?
                              descriptor.PackNames[packIndex] : "<invalid>";
            long offset = -1;
            try
            {
                if (packIndex < 0 || packIndex >= descriptor.PackInfo.Length ||
                    packIndex >= descriptor.PackNames.Length) throw new InvalidDataException("Pack index out of bounds");
                ulong packHash = GFFNV.Hash(packName);
                if (!offsetByHash.TryGetValue(packHash, out offset))
                    throw new InvalidDataException("Pack hash absent from TRPFS index");
                long length = checked((long)descriptor.PackInfo[packIndex].FileSize);
                if (length <= 0 || length > int.MaxValue || offset < 0 || offset > input.Length - length)
                    throw new InvalidDataException($"Pack offset/length outside TRPFS: {offset}, {length}");
                byte[] buffer = new byte[checked((int)length)];
                input.Position = offset;
                input.ReadExactly(buffer);
                var pack = FlatBufferConverter.DeserializeFrom<PackedArchive>(buffer);
                if (pack.FileHashes.Length != pack.FileEntry.Length)
                    throw new InvalidDataException("Packed archive hash/entry count mismatch");

                var present = new HashSet<ulong>();
                for (int j = 0; j < pack.FileHashes.Length && examined < maxFiles; j++)
                {
                    ulong hash = pack.FileHashes[j];
                    if (!group.Value.Contains(hash)) continue;
                    examined++;
                    string hashText = hash.ToString("X16");
                    present.Add(hash);
                    string? name = GFPakHashCache.GetName(hash);
                    string? relative = SafeRelativePath(name);
                    if (relative is null) relative = "_unknown/" + hashText + ".bin";
                    string target = Path.GetFullPath(Path.Combine(outputVirtual, relative.Replace('/', Path.DirectorySeparatorChar)));
                    string virtualRoot = Path.GetFullPath(outputVirtual).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
                    if (!target.StartsWith(virtualRoot, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException("Path traversal blocked: " + relative);

                    try
                    {
                        if (prior.TryGetValue(hashText, out var old) && old.Status == "OK" &&
                            old.Sha256 is not null && File.Exists(target) &&
                            Sha256File(target) == old.Sha256)
                        { skipped++; continue; }
                        var entry = pack.FileEntry[j];
                        byte[]? bytes = entry.EncryptionType != -1 ?
                            Oodle.Decompress(entry.FileBuffer, checked((long)entry.FileSize)) : entry.FileBuffer;
                        if (bytes is null) throw new InvalidDataException("Oodle decompression failed");
                        if (entry.EncryptionType != -1 && (ulong)bytes.Length != entry.FileSize)
                            throw new InvalidDataException("Decompressed size differs from entry size");
                        string digest = Sha256(bytes);
                        if (File.Exists(target))
                        {
                            if (Sha256File(target) != digest)
                                throw new IOException("Existing output differs from the native source; refusing to overwrite");
                            var existingRow = new ExportRow("OK", hashText, relative, target, digest, bytes.LongLength,
                                                            packName, offset, null);
                            log.WriteLine(JsonSerializer.Serialize(existingRow));
                            prior[hashText] = existingRow;
                            skipped++;
                            continue;
                        }
                        Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                        string tmp = target + ".za-writing";
                        if (File.Exists(tmp)) throw new IOException("Stale temporary file; inspect before retry: " + tmp);
                        File.WriteAllBytes(tmp, bytes);
                        File.Move(tmp, target);
                        var row = new ExportRow("OK", hashText, relative, target, digest, bytes.LongLength,
                                                packName, offset, null);
                        log.WriteLine(JsonSerializer.Serialize(row));
                        prior[hashText] = row;
                        ok++;
                    }
                    catch (Exception e)
                    {
                        var row = new ExportRow("FAILED", hashText, relative, target, null, 0, packName, offset,
                                                e.GetType().Name + ": " + e.Message);
                        log.WriteLine(JsonSerializer.Serialize(row));
                        prior[hashText] = row;
                        failed++;
                    }
                }
                if (examined < maxFiles)
                    foreach (ulong missing in group.Value.Where(h => !present.Contains(h)))
                    {
                        var row = new ExportRow("FAILED", missing.ToString("X16"), "_missing", null, null, 0,
                                                packName, offset, "Hash absent from decoded pack");
                        log.WriteLine(JsonSerializer.Serialize(row));
                        failed++;
                    }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"PACK FAILED {packIndex} {packName}: {ex.Message}");
                foreach (ulong hash in group.Value)
                {
                    var row = new ExportRow("FAILED", hash.ToString("X16"), "_pack_failed", null, null, 0,
                                            packName, offset, ex.GetType().Name + ": " + ex.Message);
                    log.WriteLine(JsonSerializer.Serialize(row));
                    failed++;
                }
            }
            Console.WriteLine($"Pack {packCursor}/{grouped.Count} {packName}: ok={ok}, resumed={skipped}, failed={failed}");
        }
        Console.WriteLine($"DONE: new={ok} reused={skipped} failed={failed}; log={reportPath}");
        return failed == 0 ? 0 : 1;
    }
}

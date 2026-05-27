// mpq_replace - add or replace files in an existing MPQ archive.
//
// Usage:
//   mpq_replace <archive.mpq> <root_dir>
//
// Walks <root_dir>, and for every regular file found, adds it to <archive.mpq>
// at the corresponding internal path (backslashes), replacing any existing
// entry. Existing files in the archive that are not present in <root_dir> are
// left untouched.

#include "StormLib.h"
#include "StormPort.h"

#include <cstdio>
#include <cstring>
#include <filesystem>
#include <string>
#include <system_error>
#include <vector>

namespace fs = std::filesystem;

static std::string ToMpqPath(fs::path const& rel)
{
    std::string s = rel.generic_string();      // forward slashes
    for (char& c : s)
        if (c == '/') c = '\\';                // MPQ uses backslashes
    return s;
}

int main(int argc, char** argv)
{
    if (argc != 3)
    {
        std::fprintf(stderr, "usage: %s <archive.mpq> <root_dir>\n", argv[0]);
        return 1;
    }

    char const* archivePath = argv[1];
    fs::path rootDir       = argv[2];

    if (!fs::is_directory(rootDir))
    {
        std::fprintf(stderr, "ERROR: %s is not a directory\n", argv[2]);
        return 1;
    }

    HANDLE hMpq = nullptr;
    if (!SFileOpenArchive(archivePath, 0, 0, &hMpq))
    {
        std::fprintf(stderr, "SFileOpenArchive(%s) failed: error %u\n", archivePath, SErrGetLastError());
        return 2;
    }

    // Collect all files to add (so we can show a count first).
    struct Entry { fs::path local; std::string mpq; };
    std::vector<Entry> entries;
    std::error_code ec;
    for (auto it = fs::recursive_directory_iterator(rootDir, fs::directory_options::skip_permission_denied, ec);
         it != fs::recursive_directory_iterator();
         it.increment(ec))
    {
        if (ec) { std::fprintf(stderr, "WARN: %s\n", ec.message().c_str()); ec.clear(); continue; }
        if (!it->is_regular_file()) continue;
        Entry e;
        e.local = it->path();
        e.mpq   = ToMpqPath(fs::relative(it->path(), rootDir));
        entries.push_back(std::move(e));
    }

    std::printf("Replacing %zu file(s) into %s ...\n", entries.size(), archivePath);

    int ok = 0, fail = 0;
    for (auto const& e : entries)
    {
        // Remove any existing copy first so flags (compression, etc.) are reset cleanly.
        if (SFileHasFile(hMpq, e.mpq.c_str()))
        {
            if (!SFileRemoveFile(hMpq, e.mpq.c_str(), 0))
            {
                std::fprintf(stderr, "  WARN: SFileRemoveFile(%s) failed: %u\n", e.mpq.c_str(), SErrGetLastError());
            }
        }

        DWORD dwFlags = MPQ_FILE_COMPRESS | MPQ_FILE_REPLACEEXISTING;
        DWORD dwComp  = MPQ_COMPRESSION_ZLIB;

        if (!SFileAddFileEx(hMpq, e.local.c_str(), e.mpq.c_str(), dwFlags, dwComp, dwComp))
        {
            std::fprintf(stderr, "  FAIL: %s -> %s : error %u\n",
                         e.local.string().c_str(), e.mpq.c_str(), SErrGetLastError());
            ++fail;
            continue;
        }

        std::printf("  ok: %s  (%llu bytes)\n", e.mpq.c_str(), static_cast<unsigned long long>(fs::file_size(e.local)));
        ++ok;
    }

    SFileFlushArchive(hMpq);
    SFileCloseArchive(hMpq);

    std::printf("\nDone. %d ok, %d failed.\n", ok, fail);
    return (fail == 0) ? 0 : 3;
}

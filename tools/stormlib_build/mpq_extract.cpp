// mpq_extract - extract a single file from an MPQ archive to local disk.
//
// Usage:
//   mpq_extract <archive.mpq> <mpq_internal_path> <output_local_path>
//
// Example:
//   mpq_extract patch-C.MPQ DBFilesClient\CharSections.dbc /tmp/CharSections.dbc

#include "StormLib.h"
#include "StormPort.h"

#include <cstdio>
#include <cstring>

int main(int argc, char** argv)
{
    if (argc != 4)
    {
        std::fprintf(stderr, "usage: %s <archive.mpq> <mpq_path> <output_path>\n", argv[0]);
        return 1;
    }

    char const* archivePath = argv[1];
    char const* mpqPath     = argv[2];
    char const* outPath     = argv[3];

    HANDLE hMpq = nullptr;
    if (!SFileOpenArchive(archivePath, 0, MPQ_OPEN_READ_ONLY, &hMpq))
    {
        std::fprintf(stderr, "SFileOpenArchive(%s) failed: %u\n", archivePath, SErrGetLastError());
        return 2;
    }

    if (!SFileHasFile(hMpq, mpqPath))
    {
        std::fprintf(stderr, "MPQ does not contain: %s\n", mpqPath);
        SFileCloseArchive(hMpq);
        return 3;
    }

    HANDLE hFile = nullptr;
    if (!SFileOpenFileEx(hMpq, mpqPath, 0, &hFile))
    {
        std::fprintf(stderr, "SFileOpenFileEx(%s) failed: %u\n", mpqPath, SErrGetLastError());
        SFileCloseArchive(hMpq);
        return 4;
    }

    DWORD const size = SFileGetFileSize(hFile, nullptr);

    if (!SFileExtractFile(hMpq, mpqPath, outPath, 0))
    {
        std::fprintf(stderr, "SFileExtractFile(%s -> %s) failed: %u\n", mpqPath, outPath, SErrGetLastError());
        SFileCloseFile(hFile);
        SFileCloseArchive(hMpq);
        return 5;
    }

    SFileCloseFile(hFile);
    SFileCloseArchive(hMpq);

    std::printf("ok: extracted %s (%u bytes) -> %s\n", mpqPath, size, outPath);
    return 0;
}

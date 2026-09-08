#pragma once

#ifndef NATIVE_BUILD
#include "config.h"
#include <cstdio>
#include <sys/stat.h>

// Arduino-ESP32 2.0.x LittleFS.exists() opens missing files and logs errors.
// Use the mounted VFS for expected absence (first boot and HTTP 404s).
inline bool storageFileExists(const char* path) {
    if (!path || path[0] != '/') return false;
    char fullPath[256];
    const int size = snprintf(fullPath, sizeof(fullPath), "%s%s", FILESYSTEM_MOUNT_PATH, path);
    if (size < 0 || size >= int(sizeof(fullPath))) return false;
    struct stat info;
    return stat(fullPath, &info) == 0 && S_ISREG(info.st_mode);
}
#endif

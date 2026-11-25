import sys
p = sys.argv[1]
s = open(p).read()
old = """    const auto *source = reinterpret_cast<const uint32_t *>(pixels);
    for (int32_t y = 0; y < physical_height_; ++y) {
      const int32_t source_y = static_cast<int32_t>(
          static_cast<int64_t>(y) * height_ / physical_height_);
      auto *destination = reinterpret_cast<uint32_t *>(
          surface->data + static_cast<size_t>(y) * surface->row_bytes);
      for (int32_t x = 0; x < physical_width_; ++x) {
        const int32_t source_x = static_cast<int32_t>(
            static_cast<int64_t>(x) * width_ / physical_width_);
        destination[x] = source[static_cast<size_t>(source_y) * width_ +
                                source_x];
      }
    }
"""
new = """    // Same nearest-neighbour result as before, with the column mapping computed
    // once per size instead of two 64-bit divisions for every output pixel.
    const auto *source = reinterpret_cast<const uint32_t *>(pixels);
    static std::vector<int32_t> column_map;
    if (column_map.size() != static_cast<size_t>(physical_width_)) {
      column_map.resize(static_cast<size_t>(physical_width_));
      for (int32_t x = 0; x < physical_width_; ++x)
        column_map[x] = static_cast<int32_t>(
            static_cast<int64_t>(x) * width_ / physical_width_);
    }
    const int32_t *columns = column_map.data();
    for (int32_t y = 0; y < physical_height_; ++y) {
      const int32_t source_y = static_cast<int32_t>(
          static_cast<int64_t>(y) * height_ / physical_height_);
      const uint32_t *source_row = source + static_cast<size_t>(source_y) * width_;
      auto *destination = reinterpret_cast<uint32_t *>(
          surface->data + static_cast<size_t>(y) * surface->row_bytes);
      for (int32_t x = 0; x < physical_width_; ++x)
        destination[x] = source_row[columns[x]];
    }
"""
if s.count(old) != 1:
    sys.exit("::error::PresentScaledSoftware loop not found exactly once, AERA changed")
if "#include <vector>" not in s:
    s = s.replace("#include", "#include <vector>\n#include", 1)
open(p, "w").write(s.replace(old, new))
print("patched", p)

#!/usr/bin/env bash
# Build an ImageMagick 6 shim in folder $1 for machines that only have ImageMagick 7.
# convert, identify, montage and composite log each call to $1/calls.log and run through
# ImageMagick 7's legacy (IM6 style) command parser. magick itself fails, so any code
# that still calls it is caught. Used by tests/test_im6.sh.
set -euo pipefail
dir="$1"; mkdir -p "$dir"
real="$(command -v magick)"
for tool in convert identify montage composite; do
  cat > "$dir/$tool" <<SH
#!/usr/bin/env bash
echo "$tool \$*" >> "$dir/calls.log"
exec "$real" $tool "\$@"
SH
  chmod +x "$dir/$tool"
done
cat > "$dir/magick" <<SH
#!/usr/bin/env bash
echo "magick \$*" >> "$dir/magick-calls.log"
echo "magick is not available on ImageMagick 6" >&2
exit 127
SH
chmod +x "$dir/magick"

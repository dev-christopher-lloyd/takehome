#!/usr/bin/env bash

# --- CONFIG ----------------------------------------------------
API_URL="http://localhost:8000/assets"
CAMPAIGN_ID="$1"
PRODUCT_ID="$2"
IMAGE_PATH="$3"
ASPECT_RATIO="$4"
CONTENT_TYPE="image/png"
# ---------------------------------------------------------------

# --- VALIDATION ------------------------------------------------

# Validate campaign_id
if [[ -z "$CAMPAIGN_ID" ]]; then
  echo "Error: campaign_id is required."
  echo "Usage: ./upload_image.sh <campaign_id> <product_id> <image_path> <aspect_ratio>"
  exit 1
fi

if ! [[ "$CAMPAIGN_ID" =~ ^[0-9]+$ ]]; then
  echo "Error: campaign_id must be numeric. Got: $CAMPAIGN_ID"
  exit 1
fi

# Validate product_id
if [[ -z "$PRODUCT_ID" ]]; then
  echo "Error: product_id is required."
  echo "Usage: ./upload_image.sh <campaign_id> <product_id> <image_path> <aspect_ratio>"
  exit 1
fi

if ! [[ "$PRODUCT_ID" =~ ^[0-9]+$ ]]; then
  echo "Error: product_id must be numeric. Got: $PRODUCT_ID"
  exit 1
fi

# Validate image_path
if [[ -z "$IMAGE_PATH" ]]; then
  echo "Error: image_path is required."
  echo "Usage: ./upload_image.sh <campaign_id> <product_id> <image_path> <aspect_ratio>"
  exit 1
fi

if [[ ! -f "$IMAGE_PATH" ]]; then
  echo "Error: File not found: $IMAGE_PATH"
  exit 1
fi

# Validate aspect_ratio
if [[ -z "$ASPECT_RATIO" ]]; then
  echo "Error: aspect_ratio is required (example: 1:1, 16:9, 9:16)"
  echo "Usage: ./upload_image.sh <campaign_id> <product_id> <image_path> <aspect_ratio>"
  exit 1
fi

if ! [[ "$ASPECT_RATIO" =~ ^[0-9]+:[0-9]+$ ]]; then
  echo "Error: aspect_ratio must be in the format W:H (e.g., 1:1, 16:9, 9:16). Got: $ASPECT_RATIO"
  exit 1
fi

# ---------------------------------------------------------------

echo "Encoding image..."

# macOS + Linux portable way:
BASE64_DATA=$(base64 < "$IMAGE_PATH" | tr -d '\n')

# Debug
echo "Base64 length: ${#BASE64_DATA}"

if [[ -z "$BASE64_DATA" ]]; then
  echo "ERROR: base64 encoding failed (BASE64_DATA is empty)"
  exit 1
fi

echo "Uploading to API: $API_URL"

RESPONSE=$(
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "campaign_id": $CAMPAIGN_ID,
  "product_id": $PRODUCT_ID,
  "image_base64": "$BASE64_DATA",
  "content_type": "$CONTENT_TYPE",
  "aspect_ratio": "$ASPECT_RATIO"
}
EOF
)


echo ""
echo "----- API RESPONSE -----"
echo "$RESPONSE"
echo "------------------------"


# creative automation for scalable social ad campaigns POC

## how to get started

### required packages
1. git
2. docker
3. Postman or similar program to test REST apis (optional)

### instructions
1. clone the repo
2. create .env (see .env.example)
  - if using gen ai, make sure to include gemini api key
    - GEMINI_API_KEY=<KEY>
  - if using s3, make sure to include relevant aws keys
    - S3_ACCESS_KEY=<KEY>
    - S3_SECRET_KEY=<SECRET>
    - AWS_DEFAULT_REGION=<REGION>
    - S3_BUCKET=<BUCKET>
3. run docker-compose up
4. if running minio locally, create a bucket "assets" 
  - login via http://localhost:9001/
  - username: minio, password: minio123
  - create bucket "assets"
5. use scripts or program like Postman to test REST endpoints

## assumptions

1. Brand
2. Campaign + Products
3. Social Ad Post (Image + Caption)
  - Image
    - correct aspect ratio
    - brand consistency
  - Caption
    - contains campaign message
    - localized if needed (limited capability atm)
4. Generate
  - for each campaign
    - generate localized caption if needed
    - for each product
      - for each aspect ratio
        - generate image if it doesn't exist

## happy path workflow

1. Create brand
2. Create campaign + products
3. Upload existing assets (optional)
4. Generate campaign
5. Download campaign

## curl commands for testing

```
curl --location 'http://localhost:8000/healthz'
```

```
curl --location 'http://localhost:8000/brands'
```

```
curl --location 'http://localhost:8000/brands' \
--header 'Content-Type: application/json' \
--data '{
    "name": "AquaVita Home Essentials",
    "primary_color_hex": "#2D9CDB",
    "secondary_color_hex": "#56CCF2",
    "tone_of_voice": "Clean, refreshing, reassuring",
    "font_family": "Lato",
    "consumer_good": "Eco-friendly household cleaners"
}'
```

```
curl --location 'http://localhost:8000/campaigns' \
--header 'Content-Type: application/json' \
--data '{
    "brand_id": 1,
    "name": "AquaVita FreshStart 2025",
    "products": [
        {
            "name": "AquaVita PureFoam Multi-Surface Cleaner",
            "description": "A plant-powered, streak-free cleaner designed to cut through grime while remaining gentle on your home and the planet.",
            "metadata_json": {
                "scent": "Fresh Ocean Mist",
                "bottle_size_oz": 20,
                "biodegradable": true
            }
        },
        {
            "name": "AquaVita SparkleDish Pods",
            "description": "Concentrated, water-safe dishwashing pods that lift grease, brighten glassware, and leave behind a refreshing clean aroma.",
            "metadata_json": {
                "pod_count": 42,
                "phosphate_free": true,
                "plant_based": true
            }
        }
    ],
    "target_region": "Global",
    "target_audience": "Eco-conscious households and young professionals seeking safe, effective cleaning solutions",
    "campaign_message": "Clean made simple. Refresh your home, refresh your world."
}'
```

```
curl --location --request POST 'http://localhost:8000/campaigns/1/generate'
```

```
curl --location 'http://localhost:8000/campaigns/details/1'
```

```
curl --location 'http://localhost:8000/campaigns/download/1' -o output.zip
```

```
curl --location 'http://localhost:8000/workflows/'
```
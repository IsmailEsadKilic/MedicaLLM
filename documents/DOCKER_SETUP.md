# Docker Setup for DynamoDB

## What Changed

1. **Data Persistence**: DynamoDB now saves data to `./dynamodb-data/` folder
2. **Auto Loader**: Added `data-loader` service to load all tables automatically

## Usage

### First Time Setup (Load All Data)

```bash
# Start DynamoDB and load all data
docker-compose --profile setup up

# This will:
# 1. Start DynamoDB Local
# 2. Create Conversations table
# 3. Load 17,430 drugs + 34,222 synonyms
# 4. Load 2,855,848 drug interactions
# Takes ~5-10 minutes
```

### Normal Usage (After Data is Loaded)

```bash
# Just start DynamoDB (data already loaded)
docker-compose up -d

# Stop
docker-compose down
```

### Reset Everything (Delete All Data)

```bash
# Stop containers
docker-compose down

# Delete data folder
rm -rf dynamodb-data

# Reload data
docker-compose --profile setup up
```

## Data Persistence

- Data is stored in `./dynamodb-data/` folder
- Survives container restarts
- To backup: Copy `dynamodb-data` folder
- To restore: Replace `dynamodb-data` folder

## Manual Data Loading (Alternative)

If you prefer to load data manually:

```bash
# Start only DynamoDB
docker-compose up -d dynamodb-local

# Load data with Python scripts
python3 create_conversations_table.py
python3 load_drugs_table.py
python3 load_to_dynamodb.py
```

## Troubleshooting

**Data not persisting?**
- Check if `dynamodb-data` folder exists
- Make sure you're not using `-inMemory` flag

**Loader fails?**
- Make sure XML file exists: `drugbank_data/full database 2.xml`
- Check Python scripts are in project root
- Wait 10 seconds after starting DynamoDB before loading

**Port 8000 already in use?**
- Stop existing DynamoDB: `docker-compose down`
- Or change port in docker-compose.yml

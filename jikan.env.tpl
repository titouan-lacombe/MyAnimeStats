
###
# App
###
APP_ENV=production
APP_DEBUG=false
APP_KEY=
APP_TIMEZONE=UTC
APP_URL=https://localhost:8080
APP_VERSION="4.0.0"

###
# Logging
###
LOG_CHANNEL=stack
LOG_SLACK_WEBHOOK_URL=
LOG_LEVEL=debug

###
# Database Caching (MongoDB)
###
DB_CACHING=true
DB_CONNECTION=mongodb
DB_HOST=db
DB_PORT=27017
DB_DATABASE=$DB_DATABASE
DB_ADMIN=
DB_USERNAME=$DB_USERNAME
DB_PASSWORD=$DB_PASSWORD

###
# Database query default values
###
MAX_RESULTS_PER_PAGE=25

###
# Enable MyAnimeList Heartbeat
#
# Monitor bad requests to determine whether MyAnimeList is down
#
# Fallback once the following threshold is reached
###
SOURCE=local
SOURCE_BAD_HEALTH_THRESHOLD=10
# Recheck source availability (in seconds)
SOURCE_BAD_HEALTH_RECHECK=10
# Fail count only within specified time range (in seconds)
SOURCE_BAD_HEALTH_RANGE=30
# Max Fail stores
SOURCE_BAD_HEALTH_MAX_STORE=50
# Disable failover if the score reaches the following (0.0-1.0 values ONLY)
# e.g 0.9 means 90% successful requests to MyAnimeList
SOURCE_GOOD_HEALTH_SCORE=0.9
# Max time request is allowed to take
# https://curl.haxx.se/libcurl/c/CURLOPT_TIMEOUT.html
SOURCE_TIMEOUT=10

###
# Caching (File, Redis, etc)
# Can be added over DB Caching
###
CACHING=true
CACHE_DRIVER=redis
CACHE_METHOD=database

# Caching TTL (in seconds) on specific endpoints
CACHE_DEFAULT_EXPIRE=86400 # 1 day
CACHE_META_EXPIRE=300 # 5 minutes
CACHE_USER_EXPIRE=300 # 5 minutes
CACHE_USERLIST_EXPIRE=3600 # 1 hour
CACHE_404_EXPIRE=604800 # 7 days
CACHE_SEARCH_EXPIRE=432000 # 5 days
CACHE_PRODUCERS_EXPIRE=432000 # 5 days
CACHE_MAGAZINES_EXPIRE=432000 # 5 days
CACHE_MICROCACHE_EXPIRE=60

###
# Redis Caching Configuration
###
REDIS_HOST=redis
REDIS_PASSWORD=null
REDIS_PORT=6379

###
# Micro Caching
# Uses CACHE_DRIVER
###
MICROCACHING=false
MICROCACHING_EXPIRE=5

###
# Queue management
# Uses QUEUE_CONNECTION as queue storage (MongoDB, Redis, etc)
###
QUEUE_CONNECTION=database
QUEUE_TABLE=jobs
QUEUE_FAILED_TABLE=jobs_failed
QUEUE_DELAY_PER_JOB=5

###
# Scout config
###
# For TypeSense use: typesense
#SCOUT_DRIVER=typesense
#SCOUT_QUEUE=false

###
# TypeSense Config
###
#TYPESENSE_HOST=localhost
#TYPESENSE_PORT=8108
#TYPESENSE_API_KEY=
#TYPESENSE_SEARCH_EXHAUSTIVE=true
#TYPESENSE_SEARCH_CUTTOFF_MS=450

###
# GitHub generate report URL on fatal errors
###
GITHUB_REPORTING=true
GITHUB_REST="jikan-me/jikan-rest"
GITHUB_API="jikan-me/jikan"

###
# OpenAPI
###
SWAGGER_VERSION=3.0

###
# API call insights
###
# Enable/Disable insights API system
INSIGHTS=false #WIP
# Max requests store in seconds - default 2 days
INSIGHTS_MAX_STORE_TIME=172800

###
# Error reporting
###
REPORTING=false
REPORTING_DRIVER=sentry
SENTRY_LARAVEL_DSN="https://examplePublicKey@o0.ingest.sentry.io/0"
SENTRY_TRACES_SAMPLE_RATE=0.5

###
# Endpoints
###
DISABLE_USER_LISTS=false

SCOUT_DRIVER=database

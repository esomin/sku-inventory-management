#!/bin/bash

# GPU Price Monitoring ETL System - Integration Test Script
# This script starts all system components for integration testing

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up processes..."
    
    # Stop frontend
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        log_info "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Stop backend
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        log_info "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Stop ETL scheduler
    if [ ! -z "$ETL_PID" ] && kill -0 $ETL_PID 2>/dev/null; then
        log_info "Stopping ETL scheduler (PID: $ETL_PID)..."
        kill $ETL_PID 2>/dev/null || true
    fi
    
    # Stop PostgreSQL Docker container
    log_info "Stopping PostgreSQL container..."
    cd backend && docker-compose down 2>/dev/null || true
    cd ..
    
    log_success "Cleanup completed"
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Main script
log_info "Starting GPU Price Monitoring ETL System Integration Test"
echo ""

# Step 1: Start PostgreSQL Docker container
log_info "Step 1/4: Starting PostgreSQL Docker container..."
cd backend
if docker-compose up -d; then
    log_success "PostgreSQL container started"
else
    log_error "Failed to start PostgreSQL container"
    exit 1
fi
cd ..

# Wait for PostgreSQL to be ready
log_info "Waiting for PostgreSQL to be ready..."
sleep 5
for i in {1..30}; do
    if docker exec sku-inventory-postgres pg_isready -U postgres > /dev/null 2>&1; then
        log_success "PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "PostgreSQL failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done
echo ""

# Step 2: Start Spring Boot backend
log_info "Step 2/4: Starting Spring Boot backend..."
cd backend
if [ ! -f "gradlew" ]; then
    log_error "Gradle wrapper not found in backend directory"
    exit 1
fi

# Make gradlew executable
chmod +x gradlew

# Build and start backend in background
log_info "Building backend..."
if ./gradlew build -x test > /dev/null 2>&1; then
    log_success "Backend built successfully"
else
    log_warning "Backend build had warnings, continuing..."
fi

log_info "Starting backend server..."
./gradlew bootRun > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
log_info "Waiting for backend to be ready..."
sleep 10
for i in {1..60}; do
    if curl -s http://localhost:8080/api/skus > /dev/null 2>&1; then
        log_success "Backend is ready (PID: $BACKEND_PID)"
        break
    fi
    if [ $i -eq 60 ]; then
        log_error "Backend failed to start within 60 seconds"
        log_info "Check backend.log for details"
        exit 1
    fi
    sleep 1
done
echo ""

# Step 3: Start Python ETL scheduler
log_info "Step 3/4: Starting Python ETL scheduler..."
cd etl

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
    log_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
log_info "Installing Python dependencies..."
if pip install -r requirements.txt > /dev/null 2>&1; then
    log_success "Dependencies installed"
else
    log_warning "Some dependencies may have failed to install"
fi

# Check if .env exists, if not create from template
if [ ! -f ".env" ]; then
    log_info "Creating .env file from template..."
    cp .env.template .env
    # Update database name to match backend
    sed -i.bak 's/DB_NAME=gpu_etl/DB_NAME=sku_inventory/' .env
    sed -i.bak 's/DB_PASSWORD=your_password_here/DB_PASSWORD=postgres/' .env
    rm .env.bak 2>/dev/null || true
    log_success ".env file created"
fi

# Check if scheduler.py exists
if [ -f "scheduler.py" ]; then
    log_info "Starting ETL scheduler..."
    python scheduler.py > ../etl.log 2>&1 &
    ETL_PID=$!
    log_success "ETL scheduler started (PID: $ETL_PID)"
else
    log_warning "scheduler.py not found - ETL scheduler not started"
    log_warning "This is expected if ETL implementation is not complete"
    ETL_PID=""
fi

deactivate
cd ..
echo ""

# Step 4: Start React frontend
log_info "Step 4/4: Starting React frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies..."
    if npm install > /dev/null 2>&1; then
        log_success "Frontend dependencies installed"
    else
        log_error "Failed to install frontend dependencies"
        exit 1
    fi
fi

log_info "Starting frontend development server..."
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to be ready
log_info "Waiting for frontend to be ready..."
sleep 5
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        log_success "Frontend is ready (PID: $FRONTEND_PID)"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Frontend failed to start within 30 seconds"
        log_info "Check frontend.log for details"
        exit 1
    fi
    sleep 1
done
echo ""

# Summary
log_success "=== Integration Test Environment Started ==="
echo ""
log_info "Component Status:"
echo "  ✓ PostgreSQL:     Running (localhost:5432)"
echo "  ✓ Backend API:    Running (http://localhost:8080)"
if [ ! -z "$ETL_PID" ]; then
    echo "  ✓ ETL Scheduler:  Running (PID: $ETL_PID)"
else
    echo "  ⚠ ETL Scheduler:  Not started (implementation pending)"
fi
echo "  ✓ Frontend:       Running (http://localhost:5173)"
echo ""
log_info "Log files:"
echo "  - Backend:  backend.log"
if [ ! -z "$ETL_PID" ]; then
    echo "  - ETL:      etl.log"
fi
echo "  - Frontend: frontend.log"
echo ""
log_info "Press Ctrl+C to stop all services and cleanup"
echo ""

# Keep script running
wait

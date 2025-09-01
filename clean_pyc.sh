#!/bin/bash

# Pretty __pycache__ remover with stats
# Author: Syed Taha
# Description: Finds and deletes all __pycache__ directories recursively, showing total space saved.

# Colors
GREEN="\e[32m"
RED="\e[31m"
YELLOW="\e[33m"
RESET="\e[0m"

echo -e "${YELLOW}Scanning for pycache directories...${RESET}"

# Find all __pycache__ directories
mapfile -t CACHES < <(find . -type d -name "__pycache__")

if [ ${#CACHES[@]} -eq 0 ]; then
    echo -e "${GREEN}No pycache directories found. Everything's clean!${RESET}"
    exit 0
fi

echo -e "${YELLOW}Found ${#CACHES[@]} pycache directories.${RESET}"
echo -e "${YELLOW}Calculating total size...${RESET}"

total_size=0

for dir in "${CACHES[@]}"; do
    size=$(du -sb "$dir" 2>/dev/null | cut -f1)
    total_size=$((total_size + size))
done

total_size_mb=$(echo "scale=2; $total_size / 1048576" | bc)

echo -e "${RED}Deleting pycache directories...${RESET}"

for dir in "${CACHES[@]}"; do
    echo -e " - Removing: ${dir}"
    rm -rf "$dir"
done

echo -e "${GREEN}Cleanup complete.${RESET}"
echo -e "${GREEN}Total space freed: ${total_size_mb} MB${RESET}"

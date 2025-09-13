#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from pathlib import Path

def load_stats():
    """Load statistics from JSON file"""
    with open('turn_by_turn_stats.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_averages(stats):
    """Calculate average values for each character at each turn"""
    averages = {
        'money': {},
        'nerves': {},
        'documents': {},
        'language': {},
        'items': {}
    }
    
    for turn, turn_data in stats['turns'].items():
        turn_num = int(turn)
        for char, char_data in turn_data['characters'].items():
            for resource in averages:
                if resource not in averages[char]:
                    averages[char] = {
                        'money': [],
                        'nerves': [],
                        'documents': [],
                        'language': [],
                        'items': []
                    }
                averages[char][resource].append((turn_num, char_data[resource]))
    
    # Sort by turn number
    for char in averages:
        for resource in averages[char]:
            averages[char][resource].sort(key=lambda x: x[0])
    
    return averages

def update_graph(md_content, resource, averages):
    """Update graph for specific resource in markdown content"""
    graph_pattern = f"## {resource.title()}\n\n```mermaid.*?```"
    
    # Create new graph content
    new_graph = f"## {resource.title()}\n\n```mermaid\n"
    new_graph += "%%{init: {\"theme\": \"default\", \"themeVariables\": { \"fontSize\": \"12px\"}}}%%\n"
    new_graph += "xychart-beta\n"
    new_graph += f"    title \"Средние {resource.lower()} по ходам\"\n"
    new_graph += "    x-axis [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]\n"
    
    # Y-axis ranges
    ranges = {
        'money': "0 --> 300",
        'nerves': "0 --> 10",
        'documents': "0 --> 7",
        'language': "0 --> 3",
        'items': "0 --> 3"
    }
    new_graph += f"    y-axis \"{resource.title()}\" {ranges[resource.lower()]}\n"
    
    # Add data lines
    for char, data in averages.items():
        values = data[resource.lower()]
        if values:
            # Sample 10 points evenly
            step = len(values) // 10
            sampled = values[::step][:10]  # Take first 10 points
            value_str = " ".join(str(v[1]) for v in sampled)
            char_name = char.replace(" ", "_")
            new_graph += f"    line {char_name} {value_str}\n"
    
    new_graph += "```\n"
    
    # Replace old graph with new one
    return re.sub(graph_pattern, new_graph, md_content, flags=re.DOTALL)

def main():
    # Load statistics
    stats = load_stats()
    averages = calculate_averages(stats)
    
    # Read current markdown
    md_path = Path('resource_dynamics.md')
    md_content = md_path.read_text(encoding='utf-8')
    
    # Update each graph
    for resource in ['Деньги', 'Нервы', 'Документы', 'Язык', 'Предметы']:
        md_content = update_graph(md_content, resource, averages)
    
    # Save updated markdown
    md_path.write_text(md_content, encoding='utf-8')
    print("Graphs updated successfully!")

if __name__ == '__main__':
    main()

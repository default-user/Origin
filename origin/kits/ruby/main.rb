#!/usr/bin/env ruby
# ORIGIN Ruby Kit
# Demonstrates loading and exploring ORIGIN knowledge packs
#
# Attribution: Ande + Kai (OI) + Whānau (OIs)

require 'json'

ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)"

def load_json(filename)
  path = File.join(__dir__, '..', '..', 'knowledge', 'dist', filename)
  JSON.parse(File.read(path))
end

puts "ORIGIN Kit - Ruby"
puts "================="
puts "Attribution: #{ATTRIBUTION}\n\n"

begin
  # Load index
  index = load_json('packs.index.json')
  packs = index['packs']
  puts "Loaded #{packs.length} packs from index."

  # Load graph
  graph = load_json('graph.json')
  nodes = graph['nodes']
  edges = graph['edges']
  puts "Loaded graph with #{nodes.length} nodes, #{edges.length} edges.\n\n"

  # Filter to public tier
  public_packs = packs.select { |p| p['disclosure_tier'] == 'public' }
  puts "Public tier packs (#{public_packs.length}):"
  public_packs.first(3).each do |pack|
    puts "  - #{pack['id']}: #{pack['title']}"
  end
  puts "  ... and #{public_packs.length - 3} more" if public_packs.length > 3

  # Traverse from first pack
  first_pack = packs.first
  puts "\nTraversing from #{first_pack['id']} (#{first_pack['title']}):"

  related_edges = edges.select do |e|
    e['source'] == first_pack['id'] || e['target'] == first_pack['id']
  end

  related_edges.first(3).each do |edge|
    other_id = edge['source'] == first_pack['id'] ? edge['target'] : edge['source']
    other_pack = packs.find { |p| p['id'] == other_id }
    puts "  → #{edge['type']}: #{other_id} (#{other_pack&.dig('title') || 'Unknown'})"
  end

  puts "\nAttribution: #{ATTRIBUTION}"

rescue => e
  puts "Error: #{e.message}"
end

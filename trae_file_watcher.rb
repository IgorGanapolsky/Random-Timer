#!/usr/bin/env ruby

require 'listen'
require 'pathname'

# TRAE IDE File Watcher for GitButler Integration
# This watches for file changes and triggers GitButler commits

class TraeGitButlerWatcher
  def initialize(project_path)
    @project_path = project_path
    @hook_script = File.expand_path("~/bin/trae_gitbutler_hook.rb")
    
    puts "🔍 TRAE GitButler Watcher starting..."
    puts "📁 Watching: #{@project_path}"
    puts "🔧 Hook script: #{@hook_script}"
  end
  
  def start
    listener = Listen.to(@project_path, ignore: [/.git/, /node_modules/, /.trae/]) do |modified, added, removed|
      
      # Handle modified files
      modified.each do |file|
        next if should_ignore?(file)
        puts "📝 Modified: #{file}"
        system("#{@hook_script} save '#{file}'")
      end
      
      # Handle added files
      added.each do |file|
        next if should_ignore?(file)
        puts "➕ Added: #{file}"
        system("#{@hook_script} create '#{file}'")
      end
      
      # Handle removed files
      removed.each do |file|
        next if should_ignore?(file)
        puts "🗑️  Removed: #{file}"
        system("#{@hook_script} delete '#{file}'")
      end
    end
    
    listener.start
    puts "✅ TRAE GitButler Watcher is running. Press Ctrl+C to stop."
    
    begin
      sleep
    rescue Interrupt
      puts "\n🛑 TRAE GitButler Watcher stopped."
      listener.stop
    end
  end
  
  private
  
  def should_ignore?(file)
    ignored_patterns = [
      /\.git\//,
      /node_modules\//,
      /\.trae\//,
      /\.DS_Store/,
      /\.log$/,
      /\.tmp$/,
      /\.swp$/
    ]
    
    ignored_patterns.any? { |pattern| file.match?(pattern) }
  end
end

# Start the watcher
if ARGV[0]
  project_path = ARGV[0]
else
  project_path = Dir.pwd
end

watcher = TraeGitButlerWatcher.new(project_path)
watcher.start

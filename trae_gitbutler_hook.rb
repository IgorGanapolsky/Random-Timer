#!/usr/bin/env ruby

require 'json'
require 'fileutils'

# TRAE IDE GitButler Integration Hook
# This script monitors file changes and automatically commits to GitButler

def log_message(msg)
  File.open(File.expand_path("~/trae_gitbutler.log"), "a") do |f|
    f.puts "[#{Time.now}] #{msg}"
  end
end

def get_project_root
  current_dir = Dir.pwd
  while current_dir != "/"
    if File.exist?(File.join(current_dir, ".git"))
      return current_dir
    end
    current_dir = File.dirname(current_dir)
  end
  Dir.pwd
end

def commit_to_gitbutler(file_path, action)
  project_root = get_project_root
  session_id = "trae_#{Time.now.to_i}"
  
  log_message("Committing #{file_path} (#{action}) to GitButler")
  
  Dir.chdir(project_root) do
    # Use GitButler MCP to commit changes
    commit_message = "TRAE IDE: #{action} #{File.basename(file_path)}"
    
    # Try different GitButler commit methods
    success = false
    
    # Method 1: Direct MCP call
    if system("but mcp update_branches '#{session_id}' '#{project_root}' '#{commit_message}' 2>/dev/null")
      success = true
      log_message("GitButler MCP commit successful")
    end
    
    # Method 2: GitButler CLI if MCP fails
    unless success
      if system("but commit -m '#{commit_message}' 2>/dev/null")
        success = true
        log_message("GitButler CLI commit successful")
      end
    end
    
    # Method 3: Regular git as fallback
    unless success
      system("git add '#{file_path}' && git commit -m '#{commit_message}' 2>/dev/null")
      log_message("Fallback git commit")
    end
  end
end

# Main execution
if ARGV.length >= 2
  action = ARGV[0]  # "save", "create", "delete", etc.
  file_path = ARGV[1]
  
  log_message("TRAE IDE hook triggered: #{action} #{file_path}")
  commit_to_gitbutler(file_path, action)
else
  log_message("TRAE IDE hook called with insufficient arguments")
end

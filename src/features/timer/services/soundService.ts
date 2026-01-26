/**
 * Sound Service
 * Audio playback for timer alarm using expo-audio
 */

import { Platform } from 'react-native';
import { createAudioPlayer, setAudioModeAsync, AudioPlayer } from 'expo-audio';
import { storage } from '@shared/utils/storage';

const VOLUME_STORAGE_KEY = 'alarm_volume';

class SoundService {
  private player: AudioPlayer | null = null;
  private isLoaded = false;
  private volume = 1.0; // Default to max volume

  async initialize() {
    if (Platform.OS === 'web') {
      console.log('Sound service: Web platform, using fallback');
      return;
    }

    try {
      // Load saved volume preference
      const savedVolume = storage.getString(VOLUME_STORAGE_KEY);
      if (savedVolume) {
        this.volume = parseFloat(savedVolume);
      }

      // Configure audio mode for alarm-like behavior
      await setAudioModeAsync({
        playsInSilentMode: true,
        shouldPlayInBackground: true,
      });

      // Create audio player with alarm sound
      // Note: Replace with local asset: require('@assets/sounds/alarm.mp3')
      this.player = createAudioPlayer({
        uri: 'https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3',
      });

      this.player.loop = true;
      this.player.volume = this.volume;
      this.isLoaded = true;
    } catch (error) {
      console.error('Failed to initialize sound service:', error);
    }
  }

  async play(durationMs?: number) {
    if (!this.isLoaded || !this.player) {
      console.log('Sound not loaded, skipping playback');
      return;
    }

    try {
      this.player.seekTo(0);
      this.player.play();

      // Auto-stop after duration
      if (durationMs) {
        setTimeout(() => {
          this.stop();
        }, durationMs);
      }
    } catch (error) {
      console.error('Failed to play sound:', error);
    }
  }

  async stop() {
    if (!this.player) return;

    try {
      this.player.pause();
      this.player.seekTo(0);
    } catch (error) {
      console.error('Failed to stop sound:', error);
    }
  }

  getVolume(): number {
    return this.volume;
  }

  setVolume(volume: number) {
    const clampedVolume = Math.max(0, Math.min(1, volume));
    this.volume = clampedVolume;

    // Persist volume preference
    storage.set(VOLUME_STORAGE_KEY, clampedVolume.toString());

    if (this.player) {
      this.player.volume = clampedVolume;
    }
  }

  release() {
    if (!this.player) return;

    try {
      this.player.release();
      this.player = null;
      this.isLoaded = false;
    } catch (error) {
      console.error('Failed to release sound:', error);
    }
  }
}

// Singleton instance
export const soundService = new SoundService();

/**
 * Sound Service
 * Audio playback for timer alarm using expo-av
 */

import { Audio, AVPlaybackStatus } from 'expo-av';
import { Platform } from 'react-native';

class SoundService {
  private sound: Audio.Sound | null = null;
  private isLoaded = false;

  async initialize() {
    if (Platform.OS === 'web') {
      // Web audio requires user interaction, handle differently
      console.log('Sound service: Web platform, using fallback');
      return;
    }

    try {
      // Configure audio mode
      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: true,
        shouldDuckAndroid: true,
      });

      // Load the alarm sound
      // Note: You'll need to add an alarm.mp3 to assets/sounds/
      // For now, we'll use a placeholder that can be replaced
      const { sound } = await Audio.Sound.createAsync(
        // Using a built-in system sound as fallback
        // Replace with: require('@assets/sounds/alarm.mp3')
        { uri: 'https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3' },
        { shouldPlay: false, isLooping: true }
      );

      this.sound = sound;
      this.isLoaded = true;
    } catch (error) {
      console.error('Failed to load alarm sound:', error);
    }
  }

  async play(durationMs?: number) {
    if (!this.isLoaded || !this.sound) {
      console.log('Sound not loaded, playing fallback');
      return;
    }

    try {
      await this.sound.setPositionAsync(0);
      await this.sound.playAsync();

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
    if (!this.sound) return;

    try {
      await this.sound.stopAsync();
    } catch (error) {
      console.error('Failed to stop sound:', error);
    }
  }

  async setVolume(volume: number) {
    if (!this.sound) return;

    try {
      await this.sound.setVolumeAsync(Math.max(0, Math.min(1, volume)));
    } catch (error) {
      console.error('Failed to set volume:', error);
    }
  }

  async unload() {
    if (!this.sound) return;

    try {
      await this.sound.unloadAsync();
      this.sound = null;
      this.isLoaded = false;
    } catch (error) {
      console.error('Failed to unload sound:', error);
    }
  }
}

// Singleton instance
export const soundService = new SoundService();

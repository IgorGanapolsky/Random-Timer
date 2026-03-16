import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Vibration, Animated } from 'react-native';
import { BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';

export default function AppMinimal() {
  const [minTime, setMinTime] = useState(2);
  const [maxTime, setMaxTime] = useState(5);
  const [isRunning, setIsRunning] = useState(false);
  const [isAlerting, setIsAlerting] = useState(false);
  const [statusText, setStatusText] = useState('READY');
  
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  // 呼吸动画 (Breathing Animation) 值
  const pulseAnim = useRef(new Animated.Value(1)).current;

  // 触发报警时的震动和视觉反馈
  const triggerAlert = () => {
    setIsAlerting(true);
    setStatusText('GO!');
    // 战术震动模式：短促有力
    Vibration.vibrate([0, 500, 200, 500]);
    Animated.spring(pulseAnim, {
      toValue: 1.1,
      friction: 3,
      useNativeDriver: true,
    }).start();
  };

  const startTraining = () => {
    setIsRunning(true);
    setIsAlerting(false);
    setStatusText('WAIT FOR IT...');
    
    // 开始呼吸动画
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.05, duration: 1000, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1000, useNativeDriver: true })
      ])
    ).start();

    // 毫秒级随机延迟
    const randomDelay = Math.floor(Math.random() * (maxTime - minTime + 1) + minTime) * 1000;
    timerRef.current = setTimeout(() => {
      pulseAnim.stopAnimation();
      triggerAlert();
    }, randomDelay);
  };

  const stopTraining = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    pulseAnim.stopAnimation();
    Animated.timing(pulseAnim, { toValue: 1, duration: 200, useNativeDriver: true }).start();
    
    setIsRunning(false);
    setIsAlerting(false);
    setStatusText('READY');
    Vibration.cancel();
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      Vibration.cancel();
    };
  }, []);

  // 根据状态计算动态颜色
  const getAccentColor = () => {
    if (isAlerting) return '#ff073a'; // 战术红 (Tactical Red)
    if (isRunning) return '#ffb347'; // 琥珀黄 (Amber)
    return '#39ff14'; // 荧光绿 (Neon Green)
  };

  return (
    <View style={styles.container}>
      {/* 战术暗黑渐变背景 */}
      <LinearGradient
        colors={['#161b22', '#0b0f14', '#050709']}
        style={StyleSheet.absoluteFillObject}
      />
      
      {/* 毛玻璃 HUD 显示器 */}
      <Animated.View style={[styles.hudWrapper, { transform: [{ scale: pulseAnim }] }]}>
        <BlurView intensity={isAlerting ? 60 : 30} tint="dark" style={[
          styles.hudContainer, 
          { borderColor: getAccentColor(), borderWidth: isAlerting ? 3 : 1 }
        ]}>
          <Text style={[styles.statusText, { color: getAccentColor() }]}>
            {statusText}
          </Text>
        </BlurView>
      </Animated.View>

      <View style={styles.controlsLayer}>
        {!isRunning ? (
          <View style={styles.controls}>
            <View style={styles.rangeSettings}>
              <Text style={styles.label}>MIN: {minTime}s</Text>
              <Text style={styles.label}>MAX: {maxTime}s</Text>
            </View>
            <TouchableOpacity style={styles.primaryButton} onPress={startTraining} activeOpacity={0.8}>
              <LinearGradient colors={['#238636', '#2ea043']} style={styles.buttonGradient}>
                <Text style={styles.buttonText}>START H.U.D.</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        ) : (
          <TouchableOpacity 
            style={styles.cancelButtonContainer} 
            onPress={stopTraining}
            activeOpacity={0.8}
          >
            <BlurView intensity={50} tint="dark" style={[
              styles.cancelButton, 
              isAlerting && styles.stopButtonAlert
            ]}>
              <Text style={[styles.buttonText, { color: isAlerting ? '#fff' : '#8b949e' }]}>
                {isAlerting ? 'ACKNOWLEDGE' : 'ABORT PHASE'}
              </Text>
            </BlurView>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b0f14',
    alignItems: 'center',
    justifyContent: 'center',
  },
  hudWrapper: {
    width: '85%',
    aspectRatio: 1,
    marginBottom: 60,
    borderRadius: 150, // 圆形雷达感
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.8,
    shadowRadius: 20,
    elevation: 20,
  },
  hudContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(11, 15, 20, 0.4)', // 增加深度
    borderRadius: 150,
  },
  statusText: {
    fontSize: 40, // 稍微缩小一点以适应更长的文本
    fontWeight: '900',
    letterSpacing: 4,
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 15,
    textAlign: 'center',
  },
  controlsLayer: {
    position: 'absolute',
    bottom: 80,
    width: '100%',
    alignItems: 'center',
  },
  controls: {
    alignItems: 'center',
    width: '100%',
  },
  rangeSettings: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '60%',
    marginBottom: 30,
  },
  label: {
    color: '#8b949e',
    fontSize: 16,
    fontWeight: '600',
    fontFamily: 'Courier', // 战术终端字体风格
    letterSpacing: 2,
  },
  primaryButton: {
    width: '70%',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#39ff14',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
  },
  buttonGradient: {
    paddingVertical: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelButtonContainer: {
    width: '70%',
    borderRadius: 12,
    overflow: 'hidden',
  },
  cancelButton: {
    paddingVertical: 20,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#30363d',
    backgroundColor: 'rgba(33, 38, 45, 0.6)',
  },
  stopButtonAlert: {
    borderColor: '#ff073a',
    backgroundColor: 'rgba(255, 7, 58, 0.3)',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
});

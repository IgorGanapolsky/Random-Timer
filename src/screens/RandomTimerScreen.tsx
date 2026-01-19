import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import {
  Button,
  Card,
  Text,
  TextInput,
  Title,
  Paragraph,
  Divider,
  Chip,
} from 'react-native-paper';

import { RandomTimer } from '@/utils/randomTimer';

interface TimerLog {
  id: string;
  timestamp: Date;
  message: string;
}

export const RandomTimerScreen = () => {
  const [minInterval, setMinInterval] = useState('3');
  const [maxInterval, setMaxInterval] = useState('10');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<TimerLog[]>([]);
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const timerRef = useRef<RandomTimer | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Update time remaining display
  useEffect(() => {
    if (isRunning && timerRef.current) {
      intervalRef.current = setInterval(() => {
        const remaining = timerRef.current?.getTimeRemaining() ?? null;
        setTimeRemaining(remaining);
      }, 100);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setTimeRemaining(null);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning]);

  const handleTimerTrigger = useCallback(() => {
    const newLog: TimerLog = {
      id: Date.now().toString(),
      timestamp: new Date(),
      message: `Timer triggered at ${new Date().toLocaleTimeString()}`,
    };
    setLogs((prevLogs) => [newLog, ...prevLogs.slice(0, 19)]); // Keep last 20 logs
  }, []);

  const startTimer = useCallback(() => {
    const min = parseInt(minInterval, 10) * 1000;
    const max = parseInt(maxInterval, 10) * 1000;

    if (isNaN(min) || isNaN(max) || min <= 0 || max <= 0) {
      Alert.alert('Invalid Input', 'Please enter valid positive numbers for intervals');
      return;
    }

    if (min > max) {
      Alert.alert('Invalid Range', 'Minimum interval must be less than or equal to maximum interval');
      return;
    }

    timerRef.current = new RandomTimer({
      minInterval: min,
      maxInterval: max,
      onTrigger: handleTimerTrigger,
    });

    timerRef.current.start();
    setIsRunning(true);
  }, [minInterval, maxInterval, handleTimerTrigger]);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      timerRef.current.stop();
      timerRef.current = null;
    }
    setIsRunning(false);
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        timerRef.current.stop();
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Random Timer</Title>
          <Paragraph>
            Set a random interval range and the timer will trigger events at random times within that range.
          </Paragraph>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text style={styles.label}>Interval Range (seconds)</Text>
          <View style={styles.inputRow}>
            <TextInput
              label="Min"
              value={minInterval}
              onChangeText={setMinInterval}
              keyboardType="numeric"
              mode="outlined"
              style={styles.input}
              disabled={isRunning}
            />
            <Text style={styles.separator}>to</Text>
            <TextInput
              label="Max"
              value={maxInterval}
              onChangeText={setMaxInterval}
              keyboardType="numeric"
              mode="outlined"
              style={styles.input}
              disabled={isRunning}
            />
          </View>

          {isRunning && timeRemaining !== null && (
            <Chip icon="clock-outline" style={styles.chip}>
              Next trigger in: {(timeRemaining / 1000).toFixed(1)}s
            </Chip>
          )}

          <View style={styles.buttonRow}>
            <Button
              mode="contained"
              onPress={startTimer}
              disabled={isRunning}
              style={styles.button}
            >
              Start Timer
            </Button>
            <Button
              mode="outlined"
              onPress={stopTimer}
              disabled={!isRunning}
              style={styles.button}
            >
              Stop Timer
            </Button>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.logHeader}>
            <Title>Event Log</Title>
            <Button onPress={clearLogs} disabled={logs.length === 0}>
              Clear
            </Button>
          </View>
          <Divider style={styles.divider} />
          {logs.length === 0 ? (
            <Paragraph style={styles.emptyLog}>
              No events yet. Start the timer to see events.
            </Paragraph>
          ) : (
            logs.map((log) => (
              <View key={log.id} style={styles.logItem}>
                <Text style={styles.logText}>{log.message}</Text>
              </View>
            ))
          )}
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  card: {
    marginBottom: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  input: {
    flex: 1,
  },
  separator: {
    marginHorizontal: 12,
    fontSize: 16,
  },
  chip: {
    alignSelf: 'flex-start',
    marginBottom: 16,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  button: {
    flex: 1,
  },
  logHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  divider: {
    marginVertical: 8,
  },
  emptyLog: {
    textAlign: 'center',
    fontStyle: 'italic',
    marginVertical: 16,
  },
  logItem: {
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  logText: {
    fontSize: 14,
  },
});

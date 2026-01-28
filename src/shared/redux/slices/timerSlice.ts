import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

interface TimerState {
  minTime: number;
  maxTime: number;
  isRunning: boolean;
  currentTime: number | null;
}

const initialState: TimerState = {
  minTime: 10,
  maxTime: 60,
  isRunning: false,
  currentTime: null,
};

const timerSlice = createSlice({
  name: 'timer',
  initialState,
  reducers: {
    setMinTime: (state, action: PayloadAction<number>) => {
      state.minTime = action.payload;
    },
    setMaxTime: (state, action: PayloadAction<number>) => {
      state.maxTime = action.payload;
    },
    setTimeRange: (state, action: PayloadAction<{ min: number; max: number }>) => {
      state.minTime = action.payload.min;
      state.maxTime = action.payload.max;
    },
    startTimer: (state, action: PayloadAction<number>) => {
      state.isRunning = true;
      state.currentTime = action.payload;
    },
    stopTimer: state => {
      state.isRunning = false;
    },
    resetTimer: state => {
      state.isRunning = false;
      state.currentTime = null;
    },
    tick: state => {
      if (state.currentTime !== null && state.currentTime > 0) {
        state.currentTime -= 1;
      }
    },
  },
});

export const { setMinTime, setMaxTime, setTimeRange, startTimer, stopTimer, resetTimer, tick } =
  timerSlice.actions;

export const timerReducer = timerSlice.reducer;

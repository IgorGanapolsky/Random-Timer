# Redux Instructions

applyTo: "src/shared/redux/**/*.ts"

## Slice Creation

Create slices using Redux Toolkit:
```tsx
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

type SliceState = {
  // state shape
};

const initialState: SliceState = {
  // initial values
};

export const mySlice = createSlice({
  name: 'mySlice',
  initialState,
  reducers: {
    actionName: (state, action: PayloadAction<PayloadType>) => {
      // immer-powered mutations
    },
  },
});

export const { actionName } = mySlice.actions;
export default mySlice.reducer;
```

## Using Redux in Components

ALWAYS use the typed hooks:
```tsx
// CORRECT
import { useAppDispatch, useAppSelector } from '@shared/redux';

// WRONG - untyped hooks
import { useDispatch, useSelector } from 'react-redux';
```

## Selectors

Create selectors for derived state:
```tsx
import { createSelector } from '@reduxjs/toolkit';
import type { RootState } from '@shared/redux';

export const selectDerivedValue = createSelector(
  [(state: RootState) => state.slice.value],
  (value) => computeDerivation(value)
);
```

## Persistence

For persisted state, add to whitelist in store.ts:
```tsx
const persistConfig = {
  key: 'root',
  storage: mmkvStorage,
  whitelist: ['timer', 'settings', 'newSlice'], // add here
};
```

## Async Actions

Use createAsyncThunk for async operations:
```tsx
import { createAsyncThunk } from '@reduxjs/toolkit';

export const fetchData = createAsyncThunk(
  'slice/fetchData',
  async (arg: ArgType, { rejectWithValue }) => {
    try {
      const result = await api.fetch(arg);
      return result;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);
```

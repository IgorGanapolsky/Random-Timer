import { useDispatch, useSelector, type TypedUseSelectorHook } from 'react-redux';

import type { RootState, AppDispatch } from './store';

// Use these hooks throughout the app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

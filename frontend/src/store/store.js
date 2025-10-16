import { configureStore } from '@reduxjs/toolkit'
import appSlice from './slices/appSlice'
import fileSlice from './slices/fileSlice'

export const store = configureStore({
  reducer: {
    app: appSlice,
    files: fileSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
})
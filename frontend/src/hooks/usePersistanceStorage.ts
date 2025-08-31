import { useEffect, useState } from 'react'

export function usePersistentState<T>(
  key: string,
  initialValue: T
): [T, React.Dispatch<React.SetStateAction<T>>] {
  const [state, setState] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(key)

      // Only parse if stored is valid JSON
      if (!stored || stored === 'undefined' || stored === 'null') {
        return initialValue
      }

      return JSON.parse(stored) as T
    } catch (err) {
      console.warn(`Invalid JSON for key "${key}" in localStorage`, err)
      return initialValue
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(state))
    } catch (err) {
      console.warn(`Could not save key "${key}" to localStorage`, err)
    }
  }, [key, state])

  return [state, setState]
} 

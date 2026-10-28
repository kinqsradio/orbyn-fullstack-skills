import { Stack } from 'expo-router';
export default function RootLayout() {
  return <Stack><Stack.Screen name="index" options={{ title: 'Recovery fixture' }} /><Stack.Screen name="detail" options={{ title: 'Item detail' }} /></Stack>;
}

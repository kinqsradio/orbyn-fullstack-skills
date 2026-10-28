import { Link, useLocalSearchParams } from 'expo-router';
import { Text, View } from 'react-native';
import { validItem } from '../src/contracts.mjs';
export default function Detail() {
  const { id, account } = useLocalSearchParams<{id?: string | string[]; account?: string | string[]}>();
  const item = validItem(id);
  const valid = item && typeof account === 'string' && item.startsWith(account + '-');
  return <View style={{padding: 24}}><Text accessibilityRole="header">{valid ? `Detail ${item}` : 'Invalid item — return and select again'}</Text><Text>Fixture only; route parameters do not establish authorization.</Text><Link href="/">Return to list</Link></View>;
}

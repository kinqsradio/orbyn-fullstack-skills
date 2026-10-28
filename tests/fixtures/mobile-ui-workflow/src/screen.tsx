import { useEffect, useRef, useState } from 'react';
import { FlatList, Pressable, Switch, Text, TextInput, View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Link } from 'expo-router';
import { createRecoveryController } from './contracts.mjs';
type Row = { id: string; title: string };
type State = { account: string; status: string; rows: Row[]; error: string | null };
const initial: State = {account: 'A', status: 'idle', rows: [], error: null};
export function RecoveryScreen() {
  const [state, setState] = useState<State>(initial);
  const [offline, setOffline] = useState(false);
  const [query, setQuery] = useState('');
  const offlineRef = useRef(false); offlineRef.current = offline;
  const current = useRef<ReturnType<typeof createRecoveryController> | null>(null);
  useEffect(() => {
    const controller = createRecoveryController(async (account: string, signal: AbortSignal): Promise<Row[]> => {
      await new Promise<void>((resolve, reject) => {
        const timer = setTimeout(resolve, account === 'A' ? 700 : 80);
        signal.addEventListener('abort', () => { clearTimeout(timer); reject(new Error('cancelled')); }, {once: true});
      });
      if (offlineRef.current) throw new Error('Offline fixture — retry when ready');
      return Array.from({length: 120}, (_, i) => ({id: `${account}-${i}`, title: i === 0 ? 'مرحبا · परिवार · 👩🏽‍💻 · long content for the actual row' : `Item ${i}`}));
    }, setState);
    current.current = controller; void controller.load('A');
    return () => { controller.dispose(); current.current = null; };
  }, []);
  const account = state.account;
  return <SafeAreaView style={styles.root} edges={['bottom', 'left', 'right']}>
    <Text accessibilityRole="header" style={styles.title}>Account {account}</Text>
    <Text>Synthetic transport and data. No cloud or production API.</Text>
    <View style={styles.row}><Text>Offline fixture</Text><Switch accessibilityLabel="Offline fixture" value={offline} onValueChange={setOffline} /></View>
    <TextInput accessibilityLabel="Filter items" placeholder="Filter items" value={query} onChangeText={setQuery} style={styles.input} />
    <Pressable accessibilityRole="button" onPress={() => {void current.current?.load(account === 'A' ? 'B' : 'A');}} style={styles.button}><Text>Switch account</Text></Pressable>
    <Pressable accessibilityRole="button" onPress={() => {void current.current?.load();}} style={styles.button}><Text>Retry</Text></Pressable>
    <Text accessibilityLiveRegion="polite" testID="status">{state.status}{state.error ? ': ' + state.error : ''}</Text>
    <FlatList data={state.rows.filter(row => row.title.toLocaleLowerCase().includes(query.toLocaleLowerCase()))} keyExtractor={row => row.id}
      keyboardShouldPersistTaps="handled" ListEmptyComponent={<Text>{state.status === 'ready' ? 'No matching items' : 'No current items'}</Text>}
      renderItem={({item}) => <Link href={{pathname: '/detail', params: {id: item.id, account}}} accessibilityLabel={`Open ${item.id}`} style={styles.item}><Text>{item.id} — {item.title}</Text></Link>} />
  </SafeAreaView>;
}
const styles = StyleSheet.create({root: {flex: 1, padding: 20, gap: 12}, title: {fontSize: 24, fontWeight: '700'}, row: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between'}, input: {borderWidth: 1, borderColor: '#64748b', padding: 12, borderRadius: 8, fontSize: 18}, button: {backgroundColor: '#dce8fa', padding: 12, borderRadius: 8}, item: {paddingVertical: 16, borderBottomWidth: 1, borderBottomColor: '#cad3e0'}});

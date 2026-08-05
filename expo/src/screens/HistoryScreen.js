import React, { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import api, { BASE_URL } from '../api/client';
import session from '../storage/session';

const C = {
  primary: '#1F6FEB', bg: '#F0F4FF', surface: '#FFFFFF',
  text: '#111418', muted: '#6B7280',
  danger: '#C0392B', success: '#1E8E3E',
};

function HistoryRow({ item }) {
  const phishing = item.result === 'Phishing';
  return (
    <View style={s.row}>
      <View style={[s.badge, phishing ? s.badgeDanger : s.badgeSafe]}>
        <Text style={[s.badgeText, { color: phishing ? C.danger : C.success }]}>
          {phishing ? '⚠️ Phishing' : '✅ Safe'}
        </Text>
      </View>
      <Text style={s.rowUrl} numberOfLines={1}>{item.url}</Text>
      <Text style={s.rowMeta}>
        {item.confidence.toFixed(1)}% confidence · {item.created_at?.slice(0, 10) ?? ''}
      </Text>
    </View>
  );
}

export default function HistoryScreen() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useFocusEffect(useCallback(() => { loadHistory(); }, []));

  async function loadHistory() {
    setLoading(true);
    try {
      const token = await session.getToken();
      const { ok, data } = await api.getHistory(token);
      if (ok) setItems(data.history || []);
      else Alert.alert('Error', data.error || 'Could not load history');
    } catch {
      Alert.alert('Error', 'Network error');
    } finally {
      setLoading(false);
    }
  }

  async function exportPdf() {
    if (items.length === 0) {
      Alert.alert('Nothing to export', 'Search a URL first so you have scan history to export.');
      return;
    }
    setDownloading(true);
    try {
      const token = await session.getToken();
      const dest = FileSystem.documentDirectory + `history_${Date.now()}.pdf`;
      // Send this device's screen size so the server can shape the PDF page
      // to match it — it fills the screen edge-to-edge instead of showing
      // as a cramped A4 sheet with dead space on a phone.
      const { width, height } = Dimensions.get('window');
      const url = `${BASE_URL}/api/history/pdf?w=${Math.round(width)}&h=${Math.round(height)}`;
      const { status, uri } = await FileSystem.downloadAsync(
        url, dest,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      if (status === 200) {
        const canShare = await Sharing.isAvailableAsync();
        if (canShare) {
          await Sharing.shareAsync(uri, { mimeType: 'application/pdf', dialogTitle: 'Export PDF' });
        } else {
          Alert.alert('Saved', 'PDF saved to app documents folder');
        }
      } else {
        Alert.alert('Error', 'Download failed');
      }
    } catch (e) {
      Alert.alert('Error', e.message || 'Download error');
    } finally {
      setDownloading(false);
    }
  }

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <Text style={s.headerTitle}>Scan History</Text>
      </View>
      <View style={s.actionBar}>
        <TouchableOpacity
          style={s.pdfBtn}
          onPress={exportPdf}
          disabled={downloading}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          {downloading
            ? <ActivityIndicator color="#fff" size="small" />
            : (
              <>
                <Ionicons name="download-outline" size={24} color="#fff" />
                <Text style={s.pdfBtnText}>Export PDF</Text>
              </>
            )}
        </TouchableOpacity>
      </View>

      {loading ? (
        <ActivityIndicator style={{ flex: 1 }} color={C.primary} size="large" />
      ) : items.length === 0 ? (
        <View style={s.empty}>
          <Text style={s.emptyIcon}>📋</Text>
          <Text style={s.emptyTitle}>No scans yet</Text>
          <Text style={s.emptySub}>Your URL scan history will appear here</Text>
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={i => String(i.id)}
          renderItem={({ item }) => <HistoryRow item={item} />}
          contentContainerStyle={s.list}
          onRefresh={loadHistory}
          refreshing={loading}
        />
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bg },
  header: {
    backgroundColor: C.primary, paddingHorizontal: 16, paddingVertical: 14,
  },
  headerTitle: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  actionBar: {
    backgroundColor: C.primary, paddingHorizontal: 16, paddingBottom: 16,
  },
  pdfBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9,
    minHeight: 52, backgroundColor: C.text, borderRadius: 12,
    paddingHorizontal: 20, paddingVertical: 14,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.2, shadowRadius: 4, elevation: 4,
  },
  pdfBtnText: { color: '#fff', fontSize: 18, fontWeight: '700' },
  list: { padding: 10, paddingBottom: 24 },
  row: {
    backgroundColor: C.surface, borderRadius: 12, padding: 12, marginBottom: 8,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.06, shadowRadius: 2, elevation: 1,
  },
  badge: {
    alignSelf: 'flex-start', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3,
    borderWidth: 1, marginBottom: 6,
  },
  badgeSafe: { backgroundColor: '#E8F5E9', borderColor: C.success },
  badgeDanger: { backgroundColor: '#FFEBEE', borderColor: C.danger },
  badgeText: { fontSize: 12, fontWeight: '600' },
  rowUrl: { fontSize: 13, color: C.text, marginBottom: 3 },
  rowMeta: { fontSize: 11, color: C.muted },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: { fontSize: 16, fontWeight: 'bold', color: C.muted, marginBottom: 4 },
  emptySub: { fontSize: 13, color: C.muted, textAlign: 'center' },
});

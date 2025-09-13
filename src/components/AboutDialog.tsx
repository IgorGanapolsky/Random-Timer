import React from 'react';
import { Dialog, Portal, Text, Button } from 'react-native-paper';
import { View, StyleSheet } from 'react-native';

interface AboutDialogProps {
  visible: boolean;
  onDismiss: () => void;
}

export const AboutDialog: React.FC<AboutDialogProps> = ({ visible, onDismiss }) => {
  return (
    <Portal>
      <Dialog visible={visible} onDismiss={onDismiss}>
        <Dialog.Title>About SuperPassword</Dialog.Title>
        <Dialog.Content>
          <Text variant="bodyLarge">Version 1.0.0</Text>
          <Text variant="bodyMedium" style={styles.description}>
            Your secure password manager with AI-powered features.
          </Text>
        </Dialog.Content>
        <Dialog.Actions>
          <Button onPress={onDismiss}>Close</Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
};

const styles = StyleSheet.create({
  description: {
    marginTop: 10,
  },
});

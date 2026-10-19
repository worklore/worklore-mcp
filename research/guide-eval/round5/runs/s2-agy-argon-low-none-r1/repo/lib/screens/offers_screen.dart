import 'package:flutter/material.dart';

class OffersScreen extends StatelessWidget {
  const OffersScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Offers')),
      body: ListView(
        children: const [
          ListTile(title: Text('12 months, 1.2%')),
          ListTile(title: Text('24 months, 1.1%')),
          ListTile(title: Text('36 months, 1.0%')),
        ],
      ),
    );
  }
}

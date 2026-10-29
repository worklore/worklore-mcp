import 'package:flutter/material.dart';
import '../analytics.dart';

class OfferScreen extends StatefulWidget {
  const OfferScreen({super.key});

  @override
  State<OfferScreen> createState() => _OfferScreenState();
}

class _OfferScreenState extends State<OfferScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(() {
      Analytics.capture('offers_scrolled', {'offset': _scrollController.offset});
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Offers')),
      body: ListView.builder(
        controller: _scrollController,
        itemCount: _offers.length,
        itemBuilder: (context, i) {
          final o = _offers[i];
          return ListTile(
            leading: const Icon(Icons.account_balance),
            title: Text('${o.bank}, ${o.months} months'),
            subtitle: Text('${o.rate.toStringAsFixed(1)}% APR'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {},
          );
        },
      ),
    );
  }
}

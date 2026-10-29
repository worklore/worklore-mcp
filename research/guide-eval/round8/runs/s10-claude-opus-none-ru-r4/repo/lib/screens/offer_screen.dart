import 'package:flutter/material.dart';

import '../analytics.dart';

class Offer {
  const Offer(this.bank, this.months, this.rate);
  final String bank;
  final int months;
  final double rate;
}

const _offers = [
  Offer('Norbank', 12, 9.9),
  Offer('Norbank', 24, 10.4),
  Offer('Fjordcredit', 12, 8.7),
  Offer('Fjordcredit', 36, 11.2),
  Offer('Vestkapital', 24, 9.5),
  Offer('Vestkapital', 48, 12.0),
  Offer('Sparbank', 12, 10.9),
  Offer('Sparbank', 60, 12.8),
  Offer('Nordlån', 36, 10.1),
  Offer('Nordlån', 60, 12.3),
];

class OfferScreen extends StatefulWidget {
  const OfferScreen({super.key});

  @override
  State<OfferScreen> createState() => _OfferScreenState();
}

class _OfferScreenState extends State<OfferScreen> {
  // Deepest offset already reported, so we send one event per scroll gesture
  // that goes further down instead of one per frame.
  double _maxReportedOffset = 0;

  bool _onScroll(ScrollNotification n) {
    if (n is ScrollEndNotification && n.depth == 0) {
      final offset = n.metrics.pixels;
      if (offset > _maxReportedOffset) {
        _maxReportedOffset = offset;
        Analytics.capture('offers_scrolled', {'offset': offset});
      }
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Offers')),
      body: NotificationListener<ScrollNotification>(
        onNotification: _onScroll,
        child: ListView.builder(
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
      ),
    );
  }
}

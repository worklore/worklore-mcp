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
  // Deepest offset already reported on this visit.
  double _maxReported = 0;

  // Sent when a scroll gesture ends, and only if the user got further down
  // than before, so scrolling back and forth does not flood the event quota.
  bool _onScrollEnd(ScrollEndNotification n) {
    final offset = n.metrics.pixels;
    if (offset > _maxReported) {
      _maxReported = offset;
      Analytics.capture('offers_scrolled', {'offset': offset});
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Offers')),
      body: NotificationListener<ScrollEndNotification>(
        onNotification: _onScrollEnd,
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

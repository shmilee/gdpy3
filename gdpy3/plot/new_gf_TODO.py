ax1='''
    {'layout': [111, dict(
        title="mthetamax convergence(mode4)",
        xlabel=r"$mtheta$",
        ylabel='$\gamma(L_{ne}/c_s)$',
    )],
    'data': [
        [1, 'plot', (mthetamax, growth[4]['t0.1'][100], '-o'), dict(label=r't0.1-100')],
        [2, 'plot', (mthetamax, growth[4]['t0.05'][100], '--*'), dict(label=r't0.05-100')],
        [3, 'plot', (mthetamax, growth[4]['t0.1'][200], '-o'), dict(label=r't0.1-200')],
        [4, 'plot', (mthetamax, growth[4]['t0.05'][200], '--*'), dict(label=r't0.05-200')],
        [7, 'legend', (), {}],
        [8, 'grid', (), dict(which='minor')],
    ]}
'''
print(ax1)

mthetamax=[1,2,3]
growth={4: {'t0.1': {100: [1,2,3], 200: [4,5,6]}, 't0.05': {100: [7,8,9], 200: [10,11,12]}}}
axr1=eval(ax1.replace('\n','').strip())

gf = {'Style': ['gdpy3-notebook'], 'AxesStructures': [axr1]}


